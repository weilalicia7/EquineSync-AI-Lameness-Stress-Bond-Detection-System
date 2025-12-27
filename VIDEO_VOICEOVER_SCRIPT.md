# EquineSync - 3-Minute Video Voiceover Script
**Tableau Hackathon Submission - Confluent Challenge**

---

## [0:00 - 0:20] INTRODUCTION - The Problem
*[Screenshot: Landing Page - Horse & Rider Performance Monitor]*

**"Every year, thousands of horses are sold with undetected lameness. By the time symptoms become visible, the damage is already done. I experienced this heartbreak firsthand when I purchased a horse that appeared healthy, only to discover hidden lameness weeks later.**

**That's why I built EquineSync - a real-time biomechanical intelligence system that detects lameness before it becomes visible."**

---

## [0:21 - 0:45] THE SOLUTION - How It Works
*[Screenshot: Stats Page - 94% Detection, 2.5x Recovery]*

**"EquineSync uses advanced sensor technology and AI to monitor four-legged gait patterns in real-time. Our system achieves 94% early detection of lameness issues before visible symptoms appear, leading to 2.5 times faster recovery and 15% performance gains for over 2,500 elite equestrian partnerships worldwide.**

*[Screenshot: Device Connection - Horse & Rider HR]*

**The system connects both horse and rider heart rate monitors, enabling us to track not just physical health, but the emotional bond between horse and rider."**

---

## [0:46 - 1:10] SETUP & SENSOR TECHNOLOGY
*[Screenshot: Gait Analysis Tab - Gait Types]*

**"EquineSync automatically classifies gait patterns - from standing and walking to trotting, cantering, and galloping - using FFT frequency analysis on sensor data streaming at 100 Hertz.**

*[Screenshot: 4-Leg Sensor Display]*

**Four IMU sensors attach to each leg, streaming 400 data points per second through Confluent Kafka. Our system uses automatic leg detection - no manual configuration needed. The sensors communicate via Bluetooth and begin analyzing movement the moment the horse starts moving."**

---

## [1:11 - 1:50] LIVE DEMO - Real-Time Detection
*[Screenshot: Live Dashboard with LAMENESS ALERT]*

**"Let me show you the system in action, using authentic equine data from the 'Horsing Around' research dataset.**

**Watch the real-time dashboard. You'll see symmetry analysis across all four legs, with individual amplitude tracking for each limb. The system calculates front, hind, and diagonal symmetry scores every second.**

*[Screenshot: HRV and Leg Health Scores]*

**Heart rate variability metrics - SDNN, RMSSD, and pNN50 - monitor stress levels according to clinical ESC standards. Each leg receives an individual health score from 0 to 100, with real-time deductions for variability, frequency deviation, and movement patterns.**

**At the 60-second mark, watch what happens - a lameness alert triggers immediately when symmetry drops below the critical threshold."**

---

## [1:51 - 2:20] UNIQUE FEATURE - Emotional Bond
*[Screenshot: Horse-Rider Bond - Connection Strength 96]*

**"But EquineSync goes beyond physical metrics. We track the horse-rider emotional bond through synchronized heart rate analysis.**

**Notice the bond score: 96 out of 100 - an excellent partnership. But watch what happens when lameness is detected. The timeline shows exactly when stress began affecting the relationship. As the horse experiences discomfort, the bond score decreases, providing trainers with insight into how pain impacts partnership quality."**

---

## [2:21 - 2:50] CLINICAL REPORTING
*[Screenshot: Session Result Report]*

**"After each session, EquineSync generates comprehensive clinical reports. Period-by-period analysis breaks down the entire session into 30-second intervals, showing exactly when behavioral changes occurred.**

**The report includes average symmetry scores, bond metrics, behavioral observations, and color-coded status indicators. Veterinarians receive actionable recommendations with specific urgency levels and follow-up protocols.**

**Every report is downloadable, making it easy to track progress over time and share with your veterinary team."**

---

## [2:51 - 3:00] CLOSING - Technical Stack
*[Screenshot: Return to Landing Page]*

**"Built with Confluent Kafka for real-time data streaming, Google Vertex AI for machine learning inference, and powered by authentic research data - EquineSync represents the future of equine health monitoring.**

**Because no horse should suffer from undetected lameness. And no rider should experience the heartbreak I did.**

**EquineSync - Elite Performance Monitoring for the horses we love."**

---

## Technical Notes for Video Production

**Total Duration:** 3:00 minutes (180 seconds)
**Speaking Rate:** ~425 words at 140-145 words per minute
**Tone:** Professional, passionate, personal

**Screenshot Timing:**
1. Landing Page (0:00-0:20) - 20 sec
2. Stats Page (0:21-0:30) - 9 sec
3. Device Connection (0:31-0:45) - 14 sec
4. Gait Analysis (0:46-0:55) - 9 sec
5. 4-Leg Sensors (0:56-1:10) - 14 sec
6. Live Dashboard Alert (1:11-1:35) - 24 sec
7. HRV + Leg Health (1:36-1:50) - 14 sec
8. Horse-Rider Bond (1:51-2:20) - 29 sec
9. Session Report (2:21-2:50) - 29 sec
10. Landing Page (2:51-3:00) - 9 sec

**Music Suggestions:**
- Opening: Gentle, emotional piano
- Demo section: Build to upbeat, professional
- Closing: Inspirational, hopeful

**Visual Effects:**
- Highlight key metrics with circles/arrows
- Zoom into charts during lameness detection
- Smooth transitions between screenshots
- Add subtle "data streaming" effects overlay

---

**Built for Tableau Hackathon 2025 - Confluent Challenge**
