from helpers import upload_to_orthanc, save_dicom_file, create_new_uids, check_and_set_destination
from tempfile import TemporaryDirectory
import pydicom
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from PIL import Image
import numpy
import uuid
import os
from datetime import date
import nibabel as nib
# to import project functionalities
import sys
sys.path.append('./tools')


# Conversion function for both directories and single files, destination argument is optional
def convert(path, destination='', upload=False, from_web_request=False):
    # check if path string is legit
    if os.path.isdir(path) or os.path.isfile(path):
        # to make sure that all files (within one directory) have the same context, otherwise they can't be viewed or accessed together
        uids = create_new_uids()

        # destination folder
        destination = check_and_set_destination(path, destination)

        # create zipped_file location -> for no upload (save to destination) mode, data will be zipped
        zipped_file = os.path.join(destination, "converted2dicom.zip")

        # converts a whole directory of image files to dicom
        # directory is interpreted as one dicom study + every file is interpreted as a series
        if os.path.isdir(path):
            i = 1
            for filename in os.listdir(path):
                f = os.path.join(path, filename)
                # checking if it is a file
                # extra check for endings since folders often contain additional study data in csv or different format
                if os.path.isfile(f) and (f.endswith(".jpg") or f.endswith(".bmp") or f.endswith(".png")):
                    pilfile2dicom(f, zipped_file, upload,
                                  from_web_request, uids, i)
                    i += 1
                elif os.path.isfile(f) and (f.endswith(".nii") or path.endswith(".nii.gz")):
                    # zipped_file needs renaming for every file, otherwise slices from different series end up in one directory
                    zipped_file = os.path.join(
                        destination, f"converted2dicom_{i}.zip")
                    nifti2dicom(f, zipped_file, upload,
                                from_web_request, uids, i)
                    i += 1

        # converts a single non dicom file to dicom
        elif os.path.isfile(path):
            if path.endswith(".jpg") or path.endswith(".bmp") or path.endswith(".png"):
                pilfile2dicom(path, zipped_file, upload,
                              from_web_request, uids)  # i is set to default
            elif path.endswith(".nii") or path.endswith(".nii.gz"):
                nifti2dicom(path, zipped_file, upload,
                            from_web_request, uids)  # i is set to default
        # returning the zip file is necessary for web-service, otherwise the zip was already saved in 'destination'
        return zipped_file
    else:
        raise Exception("invalid path")


# jpeg/bmp/png conversion to dicom
def pilfile2dicom(filename, zipped_file, upload, from_web_request, uids, series_index=0):
    # Load image with Pillow
    img = Image.open(filename)
    width, height = img.size

    # Convert PNG and BMP files
    if img.format == 'PNG' or img.format == 'BMP':
        img = img.convert('RGB')

    # translate grayscale or rgb image to numpy array

    if img.mode == 'L':
        np_frame = numpy.asarray(img)
    elif img.mode == 'RGBA' or img.mode == 'RGB':
        # pixel depth of RGB = 24 bit (3*8 bit) -> uint8
        np_frame = numpy.array(img.getdata(), dtype=numpy.uint8)
    else:
        raise Exception("Unknown image mode")
    # get height, width and number of channels (rgb or grayscale) and pixel depth (always 8bit per channel)
    image_properties = [height, width, np_frame.shape[1], 8]

    # convert image data to dicom format
    ds = image2dicom(np_frame, image_properties, uids, series_index)
    if upload:
        upload_to_orthanc(ds, filename, from_web_request)
    else:
        # write dicom data to zip
        save_dicom_file(ds, filename, zipped_file, "converted")


# nifti conversion to dicom, based on: https://pycad.co/nifti2dicom/
def nifti2dicom(filename, zipped_file, upload, from_web_request, uids, series_index=0):
    nifti_file = nib.load(filename)
    nifti_array = nifti_file.get_fdata()
    slices_count = nifti_array.shape[2]
    # image_properties holds [height, width, number of channels, pixel depth] and is needed for image2dicom function
    # number of channels is set to 1 since nifti files are usually grayscale (CT images), pixel depth of nifti files is usually 16 bit
    image_properties = [nifti_array.shape[0], nifti_array.shape[1], 1, 16]

    # converts and saves/uploads each slice of the nifti file (slice=instance, file=series)
    for slice in range(slices_count):
        # pixel depth of nifti files is usually 16bit
        array = nifti_array[:, :, slice].astype('uint16')
        # convert slice data to dicom format
        ds = image2dicom(array, image_properties, uids, series_index, slice)
        if upload:
            upload_to_orthanc(ds, filename, from_web_request)
        else:
            # save dicom data to destination
            # mode has extra slice parameter, so new dicom files aren't named the same
            save_dicom_file(ds, filename, zipped_file, f"converted_{slice}")


# converts and saves a non-dicom image file to dicom
# based on: https://github.com/jwitos/JPG-to-DICOM/blob/master/jpeg-to-dicom.py
def image2dicom(array, image_properties, uids, series_index, instance_index=0):
    # Create DICOM from scratch
    ds = Dataset()
    ds.file_meta = Dataset()
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
    ds.file_meta.MediaStorageSOPInstanceUID = "1.2.276.0.7230010.3.1.4.0.42382.1638878078.817218"
    ds.file_meta.ImplementationClassUID = "1.2.3.4"

    ds.Rows = image_properties[0]
    ds.Columns = image_properties[1]
    if image_properties[2] == 3:
        ds.SamplesPerPixel = 3
        ds.PhotometricInterpretation = "RGB"
    else:
        ds.SamplesPerPixel = 1
        # for inverted grayscale try "MONOCHROME"
        ds.PhotometricInterpretation = "MONOCHROME2"

    # pixel depth information
    ds.BitsStored = image_properties[3]
    ds.BitsAllocated = image_properties[3]
    ds.HighBit = image_properties[3] - 1

    ds.PixelRepresentation = 0
    ds.PlanarConfiguration = 0
    ds.NumberOfFrames = 1

    ds.SOPClassUID = uids[0]
    ds.SOPInstanceUID = str(uids[1]) + '.' + \
        str(series_index) + str(instance_index)
    ds.StudyInstanceUID = uids[2]
    # images from one directory show up as seperate series within a study
    # (remove part after first '+' to move everything into 1 series)
    ds.SeriesInstanceUID = str(uids[3]) + '.' + str(series_index)

    # important for nifti slices
    ds.InstanceNumber = instance_index

    ds.PatientName = 'Unbekannt'
    ds.PatientID = uids[4]
    ds.PatientBirthDate = ''
    ds.PatientSex = ''
    ds.PatientIdentityRemoved = 'YES'

    # sets Modality tag to 'Other'
    ds.Modality = 'OT'

    # sets study date to current timestamp (date of conversion)
    now = date.today()
    ds.StudyDate = now.strftime("%Y%m%d")

    # sets pixeldata
    ds.PixelData = array.tobytes()

    ds.is_little_endian = True
    ds.is_implicit_VR = False

    return ds


# how to use convert2dicom:

# single nifti .nii file, no upload
# convert(path=r'/home/main/Desktop/pacs2go/pacs2go/test_data/test.nii')
# single jpg file, no upload
# convert(path=r'/home/main/Desktop/images/Osteosarcoma-UT/Training-Set-2/set8/Case-48-P5-C17-7752-15521.jpg')

# directory of jpeg files, with upload to ORTHANC
# convert(path=r'/home/main/Desktop/images/Osteosarcoma-UT/Training-Set-1/set10', upload=True)
# directory of nifti filse, no upload
# convert(path=r'/home/main/Desktop/images/nifti')
