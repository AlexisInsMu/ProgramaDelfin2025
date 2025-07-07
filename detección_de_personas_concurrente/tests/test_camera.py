from src.camera.camera_manager import CameraManager
from src.camera.image_processor import ImageProcessor
import unittest
from unittest.mock import patch, MagicMock

class TestCameraModule(unittest.TestCase):

    @patch('src.camera.camera_manager.CameraManager')
    def test_camera_manager_start_stream(self, MockCameraManager):
        camera_manager = MockCameraManager.return_value
        camera_manager.start_stream()
        camera_manager.start_stream.assert_called_once()

    @patch('src.camera.image_processor.ImageProcessor')
    def test_image_processor_process_image(self, MockImageProcessor):
        image_processor = MockImageProcessor.return_value
        test_image = "test_image_data"
        processed_image = image_processor.process_image(test_image)
        image_processor.process_image.assert_called_once_with(test_image)
        self.assertEqual(processed_image, image_processor.get_processed_image.return_value)

if __name__ == '__main__':
    unittest.main()