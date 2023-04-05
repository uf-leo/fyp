import easyocr

reader = easyocr.Reader(['en'])


def detect(image):
	try:
		result = reader.readtext(image)
	except:
		return ""

	plate_number = ""
	if len(result) > 0:
		for res in result:
			plate_number += res[1]
	return plate_number.upper()
