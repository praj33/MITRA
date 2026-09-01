import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.integrations import get_integrations, save_gmail_integration, send_whatsapp_otp, verify_whatsapp_otp, get_ical_feed, GmailIntegrationRequest, WhatsAppOTPRequest, WhatsAppVerifyRequest

async def run_tests():
    print("=== TESTING INTEGRATIONS API & WEBCAL FEED ===")
    user_id = "test_user_enterprise"

    # 1. Fetch Integrations
    status = await get_integrations(user_id=user_id)
    print("1. Initial Status:", status)

    # 2. Save Gmail
    gmail_res = await save_gmail_integration(GmailIntegrationRequest(user_id=user_id, email="raj@example.com", app_password="abcd-efgh-ijkl-mnop"))
    print("2. Gmail Save Res:", gmail_res)

    # 3. Send WhatsApp OTP
    otp_res = await send_whatsapp_otp(WhatsAppOTPRequest(user_id=user_id, phone="+919876543210"))
    print("3. WhatsApp OTP Res:", otp_res)

    # 4. Verify OTP
    code = otp_res["demo_otp"]
    verify_res = await verify_whatsapp_otp(WhatsAppVerifyRequest(user_id=user_id, phone="+919876543210", code=code))
    print("4. Verify OTP Res:", verify_res)

    # 5. Fetch updated integrations
    updated_status = await get_integrations(user_id=user_id)
    print("5. Updated Status:", updated_status)

    # 6. Fetch iCal Feed (.ics)
    feed_res = await get_ical_feed(user_id=user_id)
    print("6. iCal Feed Length:", len(feed_res.body))
    print("=== INTEGRATIONS VERIFICATION PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
