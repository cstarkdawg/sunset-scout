#!/usr/bin/env python3
"""
Sunset & Transit Scout
Analyzes weather conditions and provides sunset quality scores with transit logistics
"""

import json
import requests
from datetime import datetime, timedelta
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
TAIPEI_LAT = 25.0330
TAIPEI_LON = 121.5654
OPENWEATHER_API_KEY = 'd36907b4ded84184fb553c793f400e74'

# Transit configuration
HOME_LOCATION = {
    'name': 'MRT Technology Building Station',
    'lat': 25.0260787,
    'lon': 121.5434607
}

SUNSET_SPOTS = {
    'dadaocheng': {
        'name': 'Dadaocheng Wharf',
        'lat': 25.0644,
        'lon': 121.5089,
        'transit_time_minutes': 25,
        'description': 'Riverside view with city skyline',
        'cafe': {
            'name': 'No Worries Cafe',
            'walk_from_station': '2 min walk from wharf',
            'opens': '4:00 PM',
            'why': 'Creative cocktails, right at sunset spot, opens perfectly timed'
        }
    },
    'maokong': {
        'name': 'Maokong',
        'lat': 24.9683,
        'lon': 121.5879,
        'transit_time_minutes': 50,
        'description': 'Mountain tea area with panoramic views',
        'cafe': {
            'name': 'Maokong CAFE Alley',
            'walk_from_station': '5 min from gondola station',
            'opens': '11:00 AM',
            'why': 'Tea ice cream, reasonably priced, accepts cards'
        }
    }
}

def send_email_report(report_text, score):
    """Send email with sunset report"""
    sender_email = "cstarkey5@gmail.com"  # Replace with your Gmail
    sender_password = "hxck gker derp vnqw"  # Replace with Gmail app password
    receiver_email = "cstarkey5@gmail.com"  # Replace with where you want to receive
    
    subject = f"🌅 Sunset Scout: {score}/100"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(report_text, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def get_weather_data():
    """Fetch current weather and forecast from OpenWeather API"""
    
    # Current weather
    current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={TAIPEI_LAT}&lon={TAIPEI_LON}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    # Forecast
    forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={TAIPEI_LAT}&lon={TAIPEI_LON}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        current_response = requests.get(current_url, timeout=10)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        return current_data, forecast_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None, None


def get_sunset_time():
    """Get today's sunset time for Taipei"""
    # Using a simple sunset API
    url = f"https://api.sunrise-sunset.org/json?lat={TAIPEI_LAT}&lng={TAIPEI_LON}&formatted=0"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'OK':
            sunset_utc = datetime.fromisoformat(data['results']['sunset'].replace('Z', '+00:00'))
            # Convert to Taipei time (UTC+8)
            sunset_taipei = sunset_utc + timedelta(hours=8)
            return sunset_taipei
    except:
        # Fallback to approximate sunset time
        now = datetime.now()
        return now.replace(hour=17, minute=42, second=0, microsecond=0)


def analyze_with_rules(weather_data, forecast_data, sunset_time):
    """Analyze sunset conditions using rule-based scoring (no API needed)"""
    
    # Extract weather data
    current = weather_data
    cloud_cover = current.get('clouds', {}).get('all', 0)
    humidity = current.get('main', {}).get('humidity', 0)
    visibility = current.get('visibility', 10000)
    weather_desc = current.get('weather', [{}])[0].get('description', 'unknown')
    weather_main = current.get('weather', [{}])[0].get('main', 'Clear')
    
    # Initialize score
    score = 50  # Start at neutral
    
    # CLOUD COVER SCORING (most important factor)
    if 30 <= cloud_cover <= 70:
        # Ideal range - scattered clouds
        score += 30
        cloud_analysis = f"{cloud_cover}% cloud cover - ideal scattered clouds for color reflection"
    elif 20 <= cloud_cover < 30 or 70 < cloud_cover <= 80:
        # Decent range
        score += 15
        cloud_analysis = f"{cloud_cover}% cloud cover - some clouds to catch light"
    elif cloud_cover < 20:
        # Too clear - boring sunset
        score -= 15
        cloud_analysis = f"{cloud_cover}% cloud cover - mostly clear sky, limited color potential"
    else:  # > 80%
        # Too cloudy - blocked
        score -= 25
        cloud_analysis = f"{cloud_cover}% cloud cover - heavy overcast will block colors"
    
    # HUMIDITY SCORING
    if humidity < 60:
        score += 15
        humidity_impact = "Low humidity will produce crisp, vibrant colors"
    elif 60 <= humidity < 75:
        score += 5
        humidity_impact = "Moderate humidity may add slight haze but colors still good"
    else:
        score -= 15
        humidity_impact = "High humidity will create haze and wash out colors"
    
    # VISIBILITY SCORING
    if visibility >= 10000:
        score += 10
        visibility_note = "Excellent visibility"
    elif visibility >= 5000:
        score += 0
        visibility_note = "Good visibility"
    else:
        score -= 10
        visibility_note = "Poor visibility will obscure sunset"
    
    # WEATHER CONDITION PENALTIES
    if weather_main in ['Rain', 'Drizzle', 'Thunderstorm']:
        score -= 30
        weather_penalty = "Active precipitation will block sunset views"
    elif weather_main in ['Mist', 'Fog', 'Haze']:
        score -= 20
        weather_penalty = "Fog/mist will obscure colors"
    elif weather_main == 'Clouds' and cloud_cover > 90:
        score -= 15
        weather_penalty = "Heavy overcast conditions"
    else:
        weather_penalty = None
    
    # Cap score between 0-100
    score = max(0, min(100, score))
    
    # Determine rating
    if score >= 80:
        rating = "SPECTACULAR"
        recommendation = "GO"
        best_location = "maokong"  # Worth the longer trip
    elif score >= 60:
        rating = "GOOD"
        recommendation = "GO"
        best_location = "dadaocheng"  # Closer option
    elif score >= 40:
        rating = "FAIR"
        recommendation = "MAYBE"
        best_location = "dadaocheng"
    else:
        rating = "POOR"
        recommendation = "SKIP"
        best_location = "dadaocheng"
    
    # Generate vibe check
    if score >= 80:
        vibe_check = "Expect dramatic oranges, pinks, and purples with excellent cloud positioning for maximum color"
    elif score >= 60:
        vibe_check = "Good sunset potential with warm colors and decent cloud patterns"
    elif score >= 40:
        vibe_check = "Might get some color, but conditions aren't ideal - manage expectations"
    else:
        vibe_check = "Poor conditions - expect muted colors or blocked sunset"
    
    # Generate pro tip
    if score >= 80:
        pro_tip = "Bring your best lens! Use graduated ND filter and shoot in RAW for maximum dynamic range"
    elif score >= 60:
        pro_tip = "Good opportunity for sunset photography. Arrive early to scout compositions"
    elif score >= 40:
        pro_tip = "If you go, focus on silhouettes rather than color-heavy shots"
    else:
        pro_tip = "Skip tonight and save your energy for a better sunset. Check back tomorrow!"
    
    # Build overall assessment
    assessment_parts = [cloud_analysis, humidity_impact]
    if visibility_note and visibility < 10000:
        assessment_parts.append(visibility_note)
    if weather_penalty:
        assessment_parts.append(weather_penalty)
    
    overall_assessment = ". ".join(assessment_parts)
    
    # Tomorrow outlook (simplified - just based on forecast if available)
    tomorrow_outlook = "Check conditions again tomorrow for updated forecast"
    if forecast_data and 'list' in forecast_data:
        # Look at tomorrow's forecast
        for item in forecast_data['list'][:8]:  # Next 24 hours
            forecast_time = datetime.fromtimestamp(item['dt'])
            if forecast_time.date() > sunset_time.date():
                tomorrow_clouds = item.get('clouds', {}).get('all', 0)
                if 30 <= tomorrow_clouds <= 70:
                    tomorrow_outlook = "Tomorrow shows promise with better cloud conditions forecast"
                break
    
    # Return analysis in same format as Claude would
    return {
        "score": score,
        "rating": rating,
        "vibe_check": vibe_check,
        "reasoning": {
            "cloud_analysis": cloud_analysis,
            "humidity_impact": humidity_impact,
            "overall_assessment": overall_assessment
        },
        "pro_tip": pro_tip,
        "recommendation": recommendation,
        "best_location": best_location,
        "tomorrow_outlook": tomorrow_outlook
    }


def calculate_arrival_time(sunset_time, location_key):
    """Calculate when to leave to arrive 20-25 minutes before golden hour"""
    location = SUNSET_SPOTS[location_key]
    golden_hour_start = sunset_time - timedelta(minutes=30)
    target_arrival = golden_hour_start - timedelta(minutes=5)  # 5 min buffer
    departure_time = target_arrival - timedelta(minutes=location['transit_time_minutes'])
    
    return {
        'location': location['name'],
        'departure_time': departure_time.strftime('%I:%M %p'),
        'arrival_time': target_arrival.strftime('%I:%M %p'),
        'transit_duration': location['transit_time_minutes'],
        'description': location['description']
    }


def generate_report(analysis, weather_data, sunset_time):
    """Generate the final formatted report"""
    
    if not analysis:
        return "Error: Unable to generate analysis"
    
    score = analysis.get('score', 0)
    rating = analysis.get('rating', 'UNKNOWN')
    recommendation = analysis.get('recommendation', 'SKIP')
    best_location = analysis.get('best_location', 'dadaocheng')
    
    # Get transit info for recommended location
    transit = calculate_arrival_time(sunset_time, best_location)
    
    # Build report
    report = f"""
╔═══════════════════════════════════════════════════════════════╗
║           🌅 SUNSET & TRANSIT SCOUT - TAIPEI                  ║
║           {datetime.now().strftime('%A, %B %d, %Y')}                      
╚═══════════════════════════════════════════════════════════════╝

📊 SUNSET QUALITY SCORE: {score}/100
Rating: {rating} {'✅' if score >= 80 else '⚠️' if score >= 60 else '❌'}

Golden Hour: {(sunset_time - timedelta(minutes=30)).strftime('%I:%M %p')} - {sunset_time.strftime('%I:%M %p')}
Sunset Time: {sunset_time.strftime('%I:%M %p')}

───────────────────────────────────────────────────────────────

🌤️  ATMOSPHERIC CONDITIONS

Cloud Cover: {weather_data.get('clouds', {}).get('all', 0)}%
Humidity: {weather_data.get('main', {}).get('humidity', 0)}%
Visibility: {weather_data.get('visibility', 10000)}m
Weather: {weather_data.get('weather', [{}])[0].get('description', 'N/A').title()}
Temperature: {weather_data.get('main', {}).get('temp', 0):.1f}°C

───────────────────────────────────────────────────────────────

🔍 VIBE CHECK
{analysis.get('vibe_check', 'N/A')}

ANALYSIS:
• Cloud Situation: {analysis.get('reasoning', {}).get('cloud_analysis', 'N/A')}
• Humidity Impact: {analysis.get('reasoning', {}).get('humidity_impact', 'N/A')}
• Overall: {analysis.get('reasoning', {}).get('overall_assessment', 'N/A')}

───────────────────────────────────────────────────────────────

📸 PRO-TIP
{analysis.get('pro_tip', 'N/A')}

───────────────────────────────────────────────────────────────

🚇 TRANSIT PLAN
"""
    
    if recommendation == 'GO':
        # Get cafe info
        cafe_info = SUNSET_SPOTS[best_location].get('cafe', {})
        
        report += f"""
✅ RECOMMENDED LOCATION: {transit['location']}
{transit['description']}

Departure from Technology Building Station: {transit['departure_time']}
Estimated Arrival: {transit['arrival_time']}
Transit Duration: {transit['transit_duration']} minutes

ROUTE:
"""
        if best_location == 'dadaocheng':
            report += """  → Brown Line to Zhongxiao Xinsheng
  → Transfer to Orange Line
  → Exit at Daqiaotou Station
  → 10 minute walk to wharf
"""
        else:  # maokong
            report += """  → Brown Line (or transfer to Red Line at Technology Building)
  → Red Line to Taipei Zoo Station
  → Maokong Gondola to summit
  → Enjoy tea houses with view
"""
        
        # Add cafe recommendation
        if cafe_info:
            report += f"""
☕ CAFE RECOMMENDATION: {cafe_info.get('name', 'N/A')}
{cafe_info.get('walk_from_station', 'Near station')} • Opens {cafe_info.get('opens', 'varies')}
{cafe_info.get('why', 'Great spot to wait for golden hour')}

See CAFE_GUIDE.md for full list of options!
"""
    else:
        report += f"""
⏸️  RECOMMENDATION: {recommendation}
Today's conditions don't warrant the trip. Save your time for a better sunset!

{analysis.get('tomorrow_outlook', 'Check again tomorrow for updated conditions.')}
"""
    
    report += """
───────────────────────────────────────────────────────────────
"""
    
    return report


def send_notification(score, rating, recommendation):
    """Send push notification if score is high enough"""
    # This is a placeholder - you'd integrate with actual notification service
    # Options: Twilio (SMS), Pushover, ntfy.sh, iOS Shortcuts, etc.
    
    if score >= 80:
        message = f"🌅 SPECTACULAR SUNSET ALERT! Score: {score}/100 - Head out now!"
        print(f"\n{'='*60}\n🔔 NOTIFICATION: {message}\n{'='*60}\n")
        
        # Example: Write to a file that could trigger iOS Shortcut
        notification_file = "/tmp/sunset_alert.txt"
        with open(notification_file, 'w') as f:
            f.write(f"{datetime.now().isoformat()}\n")
            f.write(f"Score: {score}\n")
            f.write(f"Rating: {rating}\n")
            f.write(f"Recommendation: {recommendation}\n")
        
        print(f"Notification file created at: {notification_file}")
        print("Configure your phone to monitor this file for alerts!")


def main():
    """Main execution function"""
    
    print("Fetching weather data...")
    current_weather, forecast_weather = get_weather_data()
    
    if not current_weather:
        print("Failed to fetch weather data. Please check your API key.")
        return 1
    
    print("Getting sunset time...")
    sunset_time = get_sunset_time()
    
    print("Analyzing conditions with rule-based scoring...")
    analysis = analyze_with_rules(current_weather, forecast_weather, sunset_time)
    
    if not analysis:
        print("Failed to generate analysis.")
        return 1
    
    # Generate and display report
    report = generate_report(analysis, current_weather, sunset_time)
    print(report)
    
    # Send notification if score is high enough
    send_notification(
        analysis.get('score', 0),
        analysis.get('rating', 'UNKNOWN'),
        analysis.get('recommendation', 'SKIP')
    )
    
    # Save report to file
    output_file = f"/Users/Curtis/Documents/AI-agents/sunset-scout/report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(output_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {output_file}")
    
    # Send email report
    send_email_report(report, analysis.get('score', 0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
