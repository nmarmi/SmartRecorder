"""Handle face recognizing"""
import os
from pathlib import Path
import face_recognition
import numpy as np


class NoKnownFaceEncodingsError(Exception):
    """Exception raised when no known face encodings are provided."""
    def __init__(self, message="No known face encodings were provided."):
        self.message = message
        super().__init__(self.message)


class FaceDetector():
    """Class that handles face recognition"""

    def __init__(self, known_faces: list[np.ndarray] = []):
        self.known_faces = known_faces

    def train_from_encodings(self, face_encodings: list[np.ndarray]):
        """add provided faces encoding to known face encodings"""
        self.known_faces.append(face_encodings)

    def train_from_images(self, faces_dir: Path):
        """
        Extract face encodings from images directory and add to known face encodings
        
        Args:
            faces_dir (Path): directory with training images
        """
        print("training model from images")
        if not faces_dir.is_dir():
            raise NotADirectoryError(f"path {faces_dir} is not a directory")

        # Loop through each image file in the specified directory
        for filename in os.listdir(faces_dir):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                # Load the image file
                image_path = os.path.join(faces_dir, filename)
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    print(f"Extracted encodings from {filename}")
                    self.known_faces.append(encodings)

    def get_known_faces(self):
        """Returns known face encodings"""
        return self.known_faces

    def detect_faces(self, frame: np.ndarray):
        """
        Detect face locations and encodings in the current frame
        
        Args:
            frame (np.ndarray): frame to analyze stored in np.ndarray
        Returns:
            face_encodings (list[np.ndarray]): list of detected face encodings
        """
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        return face_encodings


    def known_face_detected(self, detected_face_encoding):
        """
        Compare known face encodings to a single face encoding detected in a frame

        Args:
            detected_face_encoding (np.ndarray): face encoding to compare
        Returns:
            bool: True iff any known face matched with detected face encoding
        """
        if not self.known_faces:
            raise NoKnownFaceEncodingsError()

        matches = face_recognition.compare_faces(self.known_faces, detected_face_encoding)

        for match in matches:
            if any(match):
                return True
        return False

    def get_timestamps(self, frame_list: list[np.ndarray]) -> set[int]:
        """    
        Iterate through frames and save frames where known face is detected

        Args:
            frame_list (list[np.ndarrat]): List of frames (NumPy arrays) extracted from the video.
        
        Returns:
            set[int]: A set of timestamps (frame indices) where known faces were detected.
        """
        if not self.known_faces:
            raise NoKnownFaceEncodingsError()
        timestamps = set()
        for frame_index, frame in enumerate(frame_list):
            face_encodings = self.detect_faces(frame)
            # compare each detected face encoding to known faces
            for face_encoding in face_encodings:
                if self.known_face_detected(face_encoding):
                    timestamps.add(frame_index)

        return timestamps

#################################################################

    def execute_with_images(self, train_faces_dir: Path, frame_list: list[np.ndarray]) -> list[int]:
        """
        Train model on faces from images directory, and identify frames with known faces
        Args:
            train_faces_dir (Path): Directory with training images
            frame_list (list[np.ndarrat]): List of frames (NumPy arrays) extracted from the video.
        
        Returns:
            set[int]: A set of timestamps (frame indices) where known faces were detected.
        """
        self.train_from_images(train_faces_dir)
        print("extracting timestamps")
        return self.get_timestamps(frame_list)


    def execute_pretrained(self, frame_list: list[np.ndarray]) -> list[int]:
        """
        Execute pipleine with model pretrained on known faces, and identify frames with known faces
        Args:
            frame_list (list[np.ndarrat]): List of frames (NumPy arrays) extracted from the video.
        
        Returns:
            set[int]: A set of timestamps (frame indices) where known faces were detected.
        """
        return self.get_timestamps(frame_list)

    def execute_with_encodings(
            self,
            known_face_encodings: list[np.ndarray],
            frame_list: list[np.ndarray]
        ) -> list[int]:
        """
        Add known face encodings to known faces, and identify frames with known faces
        Args:
            known_face_encodings (list[np.ndarray]): list of face encodigs
            frame_list (list[np.ndarrat]): List of frames (NumPy arrays) extracted from the video.
        
        Returns:
            set[int]: A set of timestamps (frame indices) where known faces were detected.
        """
        self.train_from_encodings(known_face_encodings)
        return self.get_timestamps(frame_list)

    def execute(self, *args) -> list[int]:
        """
        Execute the pipeline based on provided arguments.
        
        Arguments:
            - (Path, list[np.ndarray]): Directory with training images and frames list.
            - (list[np.ndarray], list[np.ndarray]): Known face encodings and frames list.
            - (list[np.ndarray],): List of frames (NumPy arrays) extracted from the video.

        Returns:
            list[int]: A list of timestamps (frame indices) where known faces were detected.
        """
        signature = tuple(arg.__class__ for arg in args)
        typemap = {
            (Path, list): self.execute_with_images,
            (list, list): self.execute_with_encodings,
            (list, ): self.execute_pretrained
        }
        if signature in typemap:
            return(typemap[signature](*args))
        else:
            raise TypeError(f"Invalid type signature: {signature}. Accepted signatures are:
                            Path, list), (list, list), or (list),")

