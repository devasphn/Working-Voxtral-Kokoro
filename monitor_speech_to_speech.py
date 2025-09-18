#!/usr/bin/env python3
"""
Speech-to-Speech Performance Monitor
Real-time monitoring of the speech-to-speech conversational AI system
"""
import asyncio
import aiohttp
import time
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

class SpeechToSpeechMonitor:
    """Real-time performance monitor for speech-to-speech system"""
    
    def __init__(self, health_url: str = "http://localhost:8005"):
        self.health_url = health_url
        self.monitoring = False
        self.metrics_history: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            'latency_ms': 500,  # Alert if latency exceeds target
            'target_met_rate': 80,  # Alert if target met rate below 80%
            'gpu_memory_percent': 90,  # Alert if GPU memory above 90%
            'cpu_percent': 85,  # Alert if CPU above 85%
            'memory_percent': 90  # Alert if system memory above 90%
        }
    
    async def fetch_metrics(self) -> Dict[str, Any]:
        """Fetch current system and speech-to-speech metrics"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get general status
                async with session.get(f"{self.health_url}/status") as response:
                    if response.status == 200:
                        general_status = await response.json()
                    else:
                        general_status = {"error": f"Status endpoint returned {response.status}"}
                
                # Get speech-to-speech specific metrics
                async with session.get(f"{self.health_url}/speech-to-speech/metrics") as response:
                    if response.status == 200:
                        s2s_metrics = await response.json()
                    else:
                        s2s_metrics = {"error": f"S2S metrics endpoint returned {response.status}"}
                
                # Get performance analysis
                async with session.get(f"{self.health_url}/speech-to-speech/performance") as response:
                    if response.status == 200:
                        performance = await response.json()
                    else:
                        performance = {"error": f"Performance endpoint returned {response.status}"}
                
                return {
                    "timestamp": time.time(),
                    "general": general_status,
                    "speech_to_speech": s2s_metrics,
                    "performance": performance
                }
        
        except Exception as e:
            return {
                "timestamp": time.time(),
                "error": str(e),
                "general": {},
                "speech_to_speech": {},
                "performance": {}
            }
    
    def analyze_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metrics and generate alerts"""
        alerts = []
        status = "healthy"
        
        try:
            general = metrics.get("general", {})
            s2s = metrics.get("speech_to_speech", {})
            performance = metrics.get("performance", {})
            
            # Check system resources
            system = general.get("system", {})
            if system.get("cpu_percent", 0) > self.alert_thresholds['cpu_percent']:
                alerts.append(f"High CPU usage: {system.get('cpu_percent', 0):.1f}%")
                status = "warning"
            
            if system.get("memory_percent", 0) > self.alert_thresholds['memory_percent']:
                alerts.append(f"High memory usage: {system.get('memory_percent', 0):.1f}%")
                status = "warning"
            
            # Check GPU resources
            gpu = general.get("gpu", {})
            if gpu.get("gpu_available") and gpu.get("gpu_memory_percent", 0) > self.alert_thresholds['gpu_memory_percent']:
                alerts.append(f"High GPU memory usage: {gpu.get('gpu_memory_percent', 0):.1f}%")
                status = "warning"
            
            # Check speech-to-speech performance
            if s2s.get("enabled"):
                perf_metrics = s2s.get("performance", {})
                avg_latency = perf_metrics.get("avg_total_latency_ms", 0)
                target_met_rate = perf_metrics.get("target_met_rate_percent", 0)
                
                if avg_latency > self.alert_thresholds['latency_ms']:
                    alerts.append(f"High latency: {avg_latency:.1f}ms (target: {self.alert_thresholds['latency_ms']}ms)")
                    status = "critical" if avg_latency > self.alert_thresholds['latency_ms'] * 1.5 else "warning"
                
                if target_met_rate < self.alert_thresholds['target_met_rate']:
                    alerts.append(f"Low target met rate: {target_met_rate:.1f}% (threshold: {self.alert_thresholds['target_met_rate']}%)")
                    status = "critical" if target_met_rate < 50 else "warning"
                
                # Check component status
                components = s2s.get("components", {})
                if not components.get("voxtral_stt", {}).get("initialized", False):
                    alerts.append("Voxtral STT not initialized")
                    status = "critical"
                
                if not components.get("kokoro_tts", {}).get("initialized", False):
                    alerts.append("Kokoro TTS not initialized")
                    status = "critical"
        
        except Exception as e:
            alerts.append(f"Error analyzing metrics: {e}")
            status = "error"
        
        return {
            "status": status,
            "alerts": alerts,
            "alert_count": len(alerts)
        }
    
    def format_metrics_display(self, metrics: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Format metrics for console display"""
        timestamp = datetime.fromtimestamp(metrics["timestamp"]).strftime("%H:%M:%S")
        
        # Status indicator
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌",
            "error": "💥"
        }
        
        output = [
            f"\n{'='*80}",
            f"🎭 Speech-to-Speech Monitor - {timestamp} {status_emoji.get(analysis['status'], '❓')} {analysis['status'].upper()}",
            f"{'='*80}"
        ]
        
        # System metrics
        general = metrics.get("general", {})
        system = general.get("system", {})
        gpu = general.get("gpu", {})
        
        output.append(f"\n🖥️  SYSTEM RESOURCES:")
        output.append(f"   CPU: {system.get('cpu_percent', 0):.1f}% | Memory: {system.get('memory_percent', 0):.1f}% | Disk Free: {system.get('disk_free_gb', 0):.1f}GB")
        
        if gpu.get("gpu_available"):
            output.append(f"   GPU: {gpu.get('gpu_memory_allocated', 0):.1f}GB allocated | Memory: {gpu.get('gpu_memory_percent', 0):.1f}%")
        else:
            output.append(f"   GPU: Not available")
        
        # Speech-to-Speech metrics
        s2s = metrics.get("speech_to_speech", {})
        if s2s.get("enabled"):
            output.append(f"\n🗣️  SPEECH-TO-SPEECH PIPELINE:")
            output.append(f"   Status: {'✅ Initialized' if s2s.get('initialized') else '❌ Not Initialized'}")
            
            pipeline_status = s2s.get("pipeline_status", {})
            output.append(f"   Conversations: {pipeline_status.get('total_conversations', 0)} | Target: {pipeline_status.get('latency_target_ms', 0)}ms")
            
            # Performance metrics
            perf = s2s.get("performance", {})
            if perf:
                output.append(f"\n📊 PERFORMANCE METRICS:")
                output.append(f"   Avg Latency: {perf.get('avg_total_latency_ms', 0):.1f}ms")
                output.append(f"   STT: {perf.get('avg_stt_time_ms', 0):.1f}ms | LLM: {perf.get('avg_llm_time_ms', 0):.1f}ms | TTS: {perf.get('avg_tts_time_ms', 0):.1f}ms")
                output.append(f"   Target Met Rate: {perf.get('target_met_rate_percent', 0):.1f}%")
            
            # Component status
            components = s2s.get("components", {})
            if components:
                output.append(f"\n🔧 COMPONENTS:")
                voxtral = components.get("voxtral_stt", {})
                kokoro = components.get("kokoro_tts", {})
                output.append(f"   Voxtral STT: {'✅' if voxtral.get('initialized') else '❌'} | Kokoro TTS: {'✅' if kokoro.get('initialized') else '❌'}")
                if kokoro.get("current_voice"):
                    output.append(f"   Current Voice: {kokoro.get('current_voice')}")
        else:
            output.append(f"\n🗣️  SPEECH-TO-SPEECH: ❌ Disabled")
        
        # Performance analysis
        performance = metrics.get("performance", {})
        if performance.get("latency_analysis"):
            latency = performance["latency_analysis"]
            output.append(f"\n⚡ LATENCY ANALYSIS:")
            output.append(f"   Current: {latency.get('current_avg_ms', 0):.1f}ms | Target: {latency.get('target_ms', 0)}ms | Status: {latency.get('status', 'unknown').upper()}")
        
        # Alerts
        if analysis["alerts"]:
            output.append(f"\n🚨 ALERTS ({analysis['alert_count']}):")
            for alert in analysis["alerts"]:
                output.append(f"   ⚠️  {alert}")
        else:
            output.append(f"\n✅ No alerts - system operating normally")
        
        return "\n".join(output)
    
    async def monitor_loop(self, interval: int = 5):
        """Main monitoring loop"""
        print("🎭 Starting Speech-to-Speech Performance Monitor")
        print(f"📊 Monitoring interval: {interval} seconds")
        print(f"🔗 Health endpoint: {self.health_url}")
        print("Press Ctrl+C to stop monitoring\n")
        
        self.monitoring = True
        
        try:
            while self.monitoring:
                # Fetch metrics
                metrics = await self.fetch_metrics()
                
                # Analyze metrics
                analysis = self.analyze_metrics(metrics)
                
                # Store in history
                self.metrics_history.append({
                    "timestamp": metrics["timestamp"],
                    "metrics": metrics,
                    "analysis": analysis
                })
                
                # Keep only last 100 entries
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]
                
                # Display metrics
                display = self.format_metrics_display(metrics, analysis)
                
                # Clear screen and display
                print("\033[2J\033[H", end="")  # Clear screen
                print(display)
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Monitoring stopped by user")
            self.monitoring = False
        except Exception as e:
            print(f"\n\n❌ Monitoring error: {e}")
            self.monitoring = False

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Speech-to-Speech Performance Monitor")
    parser.add_argument("--url", default="http://localhost:8005", help="Health check URL")
    parser.add_argument("--interval", type=int, default=5, help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    monitor = SpeechToSpeechMonitor(args.url)
    await monitor.monitor_loop(args.interval)

if __name__ == "__main__":
    asyncio.run(main())
