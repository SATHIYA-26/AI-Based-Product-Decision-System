from app.services.pipeline_service import PipelineService

if __name__ == "__main__":

    sample_feedback = [
    "Login failed after update",
    "Login not working since yesterday",
    "Unable to login to my account",
    "Login page stuck at loading",
    "OTP login not working",
    "Payment failed twice",
    "Payment not processing",
    "Card payment declined",
    "UPI payment not working",
    "Transaction failed after OTP",
    "App crashes when opening profile",
    "App crash after update",
    "App closes automatically",
    "Profile section not loading"
]

    result = PipelineService.run_pipeline(sample_feedback)

    print("\n===== PIPELINE RESULT =====\n")
    print(result)
 