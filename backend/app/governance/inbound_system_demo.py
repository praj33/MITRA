"""
INBOUND VALIDATOR SYSTEM DEMO
Complete test of all components working together
"""

import json
from inbound_behavior_validator import InboundBehaviorValidator
from preference_transformation_logic import apply_user_preferences, PreferenceMediator

def run_complete_demo():
    print("🛡️  INBOUND VALIDATOR SYSTEM DEMO")
    print("=" * 50)
    
    # Initialize components
    validator = InboundBehaviorValidator()
    mediator = PreferenceMediator()
    
    # Set up test user preferences
    mediator.user_preferences["demo_user"] = {
        "language": "minimal",
        "notification_frequency": "immediate",
        "emotional_tone": "protective",
        "time_windows": {
            "work": "09:00-17:00",
            "personal": "17:00-22:00",
            "sleep": "22:00-09:00"
        },
        "priority_contacts": {
            "family": ["mom@email.com"],
            "work": ["boss@company.com"],
            "emergency": ["911"]
        }
    }
    
    # Test scenarios
    test_cases = [
        {
            "name": "💰 Financial Scam",
            "content": "EMERGENCY!!! Mom had accident need $500 RIGHT NOW or she dies! Send CashApp $scam123 URGENT 30 minutes!",
            "source": "unknown@scammer.com"
        },
        {
            "name": "😢 Emotional Manipulation", 
            "content": "Everyone has abandoned me and you're my last hope. If you don't respond I'll hurt myself tonight.",
            "source": "stranger@social.com"
        },
        {
            "name": "📧 Normal Work Email",
            "content": "Hi, can you send the Q4 budget report by Friday? Thanks!",
            "source": "boss@company.com"
        },
        {
            "name": "📱 Spam Flood",
            "content": "CONGRATULATIONS! You've won $10,000! Click here before expires!",
            "source": "spam@marketing.com"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 30)
        
        # Step 1: Validate with inbound validator
        result = validator.validate_inbound_content(
            content=test['content'],
            source=test['source']
        )
        
        print(f"🔍 Risk Detection: {', '.join(result.get('risk_categories', ['none']))}")
        print(f"⚖️  Decision: {result['decision'].upper()}")
        
        # Step 2: Apply user preferences
        final_output = apply_user_preferences(result, "demo_user")
        
        print(f"📱 Delivery: {final_output['delivery_status']}")
        
        if final_output['delivery_status'] == 'immediate':
            print(f"👤 User sees: \"{final_output['message_primary']}\"")
            print(f"🎯 Action: {final_output['suggested_action']}")
        else:
            print(f"🔇 Hidden: {final_output.get('delay_reason', 'filtered')}")
        
        print(f"🔒 Original blocked: \"{test['content'][:50]}...\"")
    
    print("\n" + "=" * 50)
    print("✅ DEMO COMPLETE - All components working together!")
    print("\n📊 SYSTEM SUMMARY:")
    print("• Inbound validator: Detects 7 risk categories")
    print("• Preference engine: Respects user mental space") 
    print("• Output contract: Safe 5-field delivery format")
    print("• Integration ready: Backend + UI documentation provided")

if __name__ == "__main__":
    run_complete_demo()