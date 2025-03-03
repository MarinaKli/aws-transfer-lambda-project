import unittest
from lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):

    def test_valid_event(self):
        """Test Lambda function with a valid EventBridge event"""
        event = {
            "detail": {
                "bucket": {"name": "test-bucket"},
                "object": {"key": "raw/testfile.txt"}
            }
        }
        context = {}
        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Successfully decrypted", response["body"])

    def test_invalid_event_structure(self):
        """Test Lambda function with an invalid event structure"""
        event = {"invalid": "data"}
        context = {}
        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response["body"], "Invalid event structure")

    def test_non_raw_file(self):
        """Test Lambda function with a file outside the 'raw/' directory"""
        event = {
            "detail": {
                "bucket": {"name": "test-bucket"},
                "object": {"key": "other/testfile.txt"}
            }
        }
        context = {}
        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["body"], "File not in raw directory, skipping")

if __name__ == "__main__":
    unittest.main()