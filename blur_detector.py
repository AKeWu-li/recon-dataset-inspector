import cv2


def calculate_blur_score(image_path):
    img = cv2.imread(str(image_path))

    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

    return blur_score