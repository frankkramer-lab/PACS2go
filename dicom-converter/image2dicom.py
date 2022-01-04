from numpy.lib.type_check import real_if_close
import pydicom
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from PIL import Image
import numpy
import uuid
import os
from datetime import date


# Conversion function for both directories and single files
def convert(path, destination=''):
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

        # converts a whole directory of image files to dicom
        # directory is interpreted as one dicom study + every file is interpreted as a series
        if os.path.isdir(path):
            i = 1
            # destination folder
            if destination == '':
                destination = os.path.join(path, 'converted2dicom')
                if not os.path.exists(destination):
                    os.mkdir(destination)

            for filename in os.listdir(path):
                f = os.path.join(path, filename)

                # checking if it is a file 
                # extra check for endings since folders often contain additional study data in csv or different format
                if os.path.isfile(f) and (f.endswith(".jpg") or f.endswith(".bmp") or f.endswith(".png")):
                    image2dicom(f, uids, destination, i)
                    i += 1

        # converts a single non dicom file to dicom
        elif os.path.isfile(path):
             # destination folder
            if destination == '':
                dir_path = os.path.dirname(path) # path string without file
                destination = os.path.join(dir_path, 'converted2dicom')
                if not os.path.exists(destination):
                    os.mkdir(destination)

            image2dicom(path, uids, destination) # i is set to default
    else:
        print("invalid path")


# converts a non-dicom image file to dicom
# based on: https://github.com/jwitos/JPG-to-DICOM/blob/master/jpeg-to-dicom.py
def image2dicom(filename, uids, destination='', i=0):
    # Your input file here
    INPUT_FILE = filename

    # Name for output DICOM
    dicomized_filename = os.path.join(destination, f'{str(uuid.uuid4())}.dcm')

    # Load image with Pillow
    img = Image.open(INPUT_FILE)
    width, height = img.size
    print(f"File format is {img.format} and size: {width}, {height}, mode: {img.mode}")

    # Convert PNG and BMP files
    if img.format == 'PNG' or img.format == 'BMP':
        img = img.convert('RGB')

    # translate grayscale or rgb image to numpy array
    if img.mode == 'L':
        np_frame = numpy.asarray(img)
    elif img.mode == 'RGBA' or img.mode == 'RGB':
        np_frame = numpy.array(img.getdata(), dtype=numpy.uint8)
    else:
        print("Unknown image mode")
        return

    # Create DICOM from scratch
    ds = Dataset()
    ds.file_meta = Dataset()
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
    ds.file_meta.MediaStorageSOPInstanceUID = "1.2.276.0.7230010.3.1.4.0.42382.1638878078.817218"
    ds.file_meta.ImplementationClassUID = "1.2.3.4"

    ds.Rows = img.height
    ds.Columns = img.width
    if np_frame.shape[1] == 3:
        ds.SamplesPerPixel = 3
        ds.PhotometricInterpretation = "RGB"
    else:
        ds.SamplesPerPixel = 1
        # for inverted grayscale try "MONOCHROME"
        ds.PhotometricInterpretation = "MONOCHROME2"

    ds.BitsStored = 8
    ds.BitsAllocated = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PlanarConfiguration = 0
    ds.NumberOfFrames = 1

    ds.SOPClassUID = uids[0]
    ds.SOPInstanceUID = str(uids[1]) + '.' + str(i)
    ds.StudyInstanceUID = uids[2]
    # images from one folder show up as seperate series within a study
    # (remove part after first '+' to move everything into 1 series)
    ds.SeriesInstanceUID = str(uids[3]) + '.' + str(i)

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
    ds.PixelData = np_frame.tobytes()

    ds.is_little_endian = True
    ds.is_implicit_VR = False

    ds.save_as(dicomized_filename, write_like_original=False)


# convert(path=r'/home/main/Desktop/images/Osteosarcoma-UT/Training-Set-1/set11/P9-B6-19328-19600.jpg')
