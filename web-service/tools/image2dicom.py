import pydicom
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from PIL import Image
import numpy
import uuid
import os
from datetime import date
import nibabel as nib
import sys
sys.path.insert(0, '/home/main/Desktop/pacs2go/pacs2go/tools')
from helpers import upload_to_orthanc


# Conversion function for both directories and single files, destination argument is optional
def convert(path, destination='', upload=False):
    # check if path string is legit
    if os.path.isdir(path) or os.path.isfile(path):
        # to make sure that all files (within one directory) have the same context, otherwise they can't be viewed or accessed together
        SOPClassUID = generate_uid()
        SOPInstanceUID = generate_uid()
        StudyInstanceUID = generate_uid()
        SeriesInstanceUID = generate_uid()
        PatientID = str(uuid.uuid4())

        uids = [SOPClassUID, SOPInstanceUID,
                StudyInstanceUID, SeriesInstanceUID, PatientID]

        # destination folder
        if destination == '':
            if os.path.isfile(path):
                dir_path = os.path.dirname(path)  # path string without file
                destination = os.path.join(dir_path, 'converted2dicom')
            else:
                destination = os.path.join(path, 'converted2dicom')

            if not os.path.exists(destination):
                os.mkdir(destination)

        # converts a whole directory of image files to dicom
        # directory is interpreted as one dicom study + every file is interpreted as a series
        if os.path.isdir(path):
            i = 1
            for filename in os.listdir(path):
                f = os.path.join(path, filename)
                # checking if it is a file
                # extra check for endings since folders often contain additional study data in csv or different format
                if os.path.isfile(f) and (f.endswith(".jpg") or f.endswith(".bmp") or f.endswith(".png")):
                    pilfile2dicom(f, destination, upload, uids, i)
                    i += 1
                elif os.path.isfile(f) and f.endswith(".nii"):
                    nifti2dicom(f, destination, upload, uids, i)
            print("done")

        # converts a single non dicom file to dicom
        elif os.path.isfile(path):
            if path.endswith(".jpg") or path.endswith(".bmp") or path.endswith(".png"):
                pilfile2dicom(path, destination, upload, uids)  # i is set to default
            elif path.endswith(".nii"):
                nifti2dicom(path, destination, upload, uids)  # i is set to default
    else:
        raise Exception("invalid path")


# jpeg/bmp/png conversion to dicom
def pilfile2dicom(filename, destination, upload, uids, series_index=0):
    # Load image with Pillow
    img = Image.open(filename)
    height, width = img.size

    # Convert PNG and BMP files
    if img.format == 'PNG' or img.format == 'BMP':
        img = img.convert('RGB')

    # translate grayscale or rgb image to numpy array
    if img.mode == 'L':
        np_frame = numpy.asarray(img)
    elif img.mode == 'RGBA' or img.mode == 'RGB':
        np_frame = numpy.array(img.getdata(), dtype=numpy.uint8)
    else:
        raise Exception("Unknown image mode")
    shape = [height, width, np_frame.shape[1]]

    ds = image2dicom(np_frame, shape, uids, series_index)
    if upload:
        upload_to_orthanc(ds, filename)
    else:
        save_dicom_file(ds, filename, destination)


# nifti conversion to dicom, based on: https://pycad.co/nifti2dicom/
def nifti2dicom(filename, destination, upload, uids, series_index=0):
    nifti_file = nib.load(filename)
    nifti_array = nifti_file.get_fdata()
    slices_count = nifti_array.shape[2]
    shape = [nifti_array.shape[0], nifti_array.shape[1], nifti_array.shape[3]]
    # converts and saves each slice of the nifti file (slice=instance, file=series/study)
    for slice in range(slices_count):
        array = nifti_array[:, :, slice].astype('uint16')
        ds = image2dicom(array, shape, uids, series_index, slice, nifti=True)
        if upload:
            upload_to_orthanc(ds, filename)
        else:
            save_dicom_file(ds, filename, destination)



# converts and saves a non-dicom image file to dicom
# based on: https://github.com/jwitos/JPG-to-DICOM/blob/master/jpeg-to-dicom.py
def image2dicom(array, arr_shape, uids, series_index, instance_index=0, nifti=False):
    # Create DICOM from scratch
    ds = Dataset()
    ds.file_meta = Dataset()
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
    ds.file_meta.MediaStorageSOPInstanceUID = "1.2.276.0.7230010.3.1.4.0.42382.1638878078.817218"
    ds.file_meta.ImplementationClassUID = "1.2.3.4"

    ds.Rows = arr_shape[0]
    ds.Columns = arr_shape[1]
    if arr_shape[2] == 3:
        ds.SamplesPerPixel = 3
        ds.PhotometricInterpretation = "RGB"
    else:
        ds.SamplesPerPixel = 1
        # for inverted grayscale try "MONOCHROME"
        ds.PhotometricInterpretation = "MONOCHROME2"

    if nifti:
        # nifti needs uint16 for display
        ds.BitsStored = 16
        ds.BitsAllocated = 16
        ds.HighBit = 15
    else:
        # pathology images need uint8
        ds.BitsStored = 8
        ds.BitsAllocated = 8
        ds.HighBit = 7
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


def save_dicom_file(ds, path, destination):
    # save converted file
    dicomized_filename = os.path.join(
        destination, f'converted_{str(uuid.uuid4())}.dcm')
    ds.save_as(dicomized_filename)


# convert(path=r'/home/main/Desktop/images/nifti/1010_brain_mr_02.nii', upload=True)
# convert(path=r'/home/main/Desktop/images/Osteosarcoma-UT/Training-Set-1/set10/Case-48-P5-C25-41901-28675.jpg', upload=True)
