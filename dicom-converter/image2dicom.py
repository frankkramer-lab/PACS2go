import pydicom
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from PIL import Image
import numpy
import uuid
import os


def convert(path, destination=''):
    if os.path.isdir(path):
        convertDirectory(path, destination)
    elif os.path.isfile(path):
        convertDirectory(path, destination)
    else:
        print("invalid path")


# converts a whole directory of jpg files to dicom
# directory is interpreted as one dicom series + every file in it is an instance of said series
def convertDirectory(directory, destination=''):
    i = 1

    # to make sure that all files within one directory have the same context (otherwise they can't be viewed or accessed together)
    SOPClassUID = generate_uid()
    SOPInstanceUID = generate_uid()
    StudyInstanceUID = generate_uid()
    SeriesInstanceUID = generate_uid()

    uids = [SOPClassUID, SOPInstanceUID, StudyInstanceUID, SeriesInstanceUID]

    # destination folder
    if destination == '':
        destination = os.path.join(directory, 'converted')
        if not os.path.exists(destination):
            os.mkdir(destination)

    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)

        # checking if it is a file

        if os.path.isfile(f) and f.endswith(".jpg"):
            image2dicom(f, uids, i, destination)
            i += 1


# converts a single non dicom file
def convertFile(filename, destination=''):
    SOPClassUID = generate_uid()
    SOPInstanceUID = generate_uid()
    StudyInstanceUID = generate_uid()
    SeriesInstanceUID = generate_uid()
    uids = [SOPClassUID, SOPInstanceUID, StudyInstanceUID, SeriesInstanceUID]

    # destination folder
    if destination == '':
        real_path = os.path.realpath(filename)
        dir_path = os.path.dirname(real_path)
        destination = os.path.join(dir_path, 'converted')
        if not os.path.exists(destination):
            os.mkdir(destination)

    image2dicom(filename, uids, destination)


# converts a non-dicom image file to dicom
# based on: https://github.com/jwitos/JPG-to-DICOM/blob/master/jpeg-to-dicom.py
def image2dicom(filename, uids, i=0, destination=''):
    # Your input file here
    INPUT_FILE = filename

    # Name for output DICOM
    dicomized_filename = os.path.join(destination, f'{str(uuid.uuid4())}.dcm')
    # print(dicomized_filename)

    # Load image with Pillow
    img = Image.open(INPUT_FILE)
    width, height = img.size
    print("File format is {} and size: {}, {}, mode: {}".format(
        img.format, width, height, img.mode))

    # Convert PNG and BMP files TODO: test
    if img.format == 'PNG' or img.format == 'BMP':
        img = img.convert('RGB')

    # TODO: test different files
    # so far: tested for monochrome and rgb jpegs
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
    ds.PatientID = ''
    ds.PatientBirthDate = ''
    ds.PatientSex = ''

    # sets Modality tag to 'Other'
    ds.Modality = 'OT'
    ds.StudyDate = '19000101'

    # sets pixeldata
    ds.PixelData = np_frame.tobytes()

    ds.is_little_endian = True
    ds.is_implicit_VR = False

    ds.save_as(dicomized_filename, write_like_original=False)


convert(
    r'/home/main/Desktop/images/Osteosarcoma-UT/Training-Set-1/set4')
