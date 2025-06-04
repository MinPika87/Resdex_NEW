"""
Evaluation script for ResDex Agent system.
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from pathlib import Path

from resdex_agent.agent import ResDexRootAgent
from resdx_agent.config import AgentConfig
from google.adk.core.content import Content


class AgentEvaluator:
    """Evaluator for ResDex Agent performance and accuracy."""
    
    def __init__(self):
        self.config = AgentConfig.from_env()
        self.agent = ResDexRootAgent(self.config)
        self.test_data = self._load_test_data()
        self.results = []
    
    def _load_test_data(self) -> List[Dict[str, Any]]:
        """Load evaluation test data."""
        test_file = Path(__file__).parent / "test_data" / "search_modification_test.json"
        
        if test_file.exists():
            with open(test_file, 'r') as f:
                return json.load(f)
        else:
            # Return sample test data if file doesn't exist
            return [
                {
                    "user_input": "add python as mandatory",
                    "expected_action": "add_skill",
                    "expected_value": "Python",
                    "expected_mandatory": True,
                    "expected_trigger_search": False
                },
                {
                    "user_input": "search with java and react",
                    "expected_actions": ["add_skill", "add_skill"],
                    "expected_values": ["Java", "React"],
                    "expected_trigger_search": True
                }
            ]
    
    async def run_evaluation(self) -> Dict[str, Any]:
        """Run complete evaluation suite."""
        print("🧪 Starting ResDex Agent Evaluation...")
        
        # Test cases
        intent_accuracy = await self._evaluate_intent_recognition()
        response_quality = await self._evaluate_response_quality()
        performance_metrics = await self._evaluate_performance()
        system_health = await self._evaluate_system_health()
        
        # Compile results
        overall_results = {
            "intent_accuracy": intent_accuracy,
            "response_quality": response_quality,
            "performance_metrics": performance_metrics,
            "system_health": system_health,
            "overall_score": self._calculate_overall_score(
                intent_accuracy, response_quality, performance_metrics, system_health
            )
        }
        
        # Save results
        self._save_results(overall_results)
        
        print("✅ Evaluation completed!")
        return overall_results
    
    async def _evaluate_intent_recognition(self) -> Dict[str, Any]:
        """Evaluate intent recognition accuracy."""
        print("📝 Evaluating intent recognition...")
        
        correct_predictions = 0
        total_predictions = 0
        detailed_results = []
        
        for test_case in self.test_data:
            try:
                content = Content(data={
                    "request_type": "search_interaction",
                    "user_input": test_case["user_input"],
                    "session_state": {"keywords": []}
                })
                
                result = await self.agent.execute(content)
                
                if result.data["success"]:
                    intent_data = result.data.get("intent_data", {})
                    
                    # Check if prediction matches expected
                    if isinstance(intent_data, list):
                        # Multiple intents
                        predicted_actions = [intent.get("action") for intent in intent_data]
                        expected_actions = test_case.get("expected_actions", [])
                        is_correct = predicted_actions == expected_actions
                    else:
                        # Single intent
                        predicted_action = intent_data.get("action")
                        expected_action = test_case.get("expected_action")
                        is_correct = predicted_action == expected_action
                    
                    if is_correct:
                        correct_predictions += 1
                    
                    detailed_results.append({
                        "input": test_case["user_input"],
                        "predicted": intent_data,
                        "expected": {k: v for k, v in test_case.items() if k.startswith("expected_")},
                        "correct": is_correct
                    })
                
                total_predictions += 1
                
            except Exception as e:
                detailed_results.append({
                    "input": test_case["user_input"],
                    "error": str(e),
                    "correct": False
                })
                total_predictions += 1
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        return {
            "accuracy": accuracy,
            "correct_predictions": correct_predictions,
            "total_predictions": total_predictions,
            "detailed_results": detailed_results
        }
    
    async def _evaluate_response_quality(self) -> Dict[str, Any]:
        """Evaluate response quality and helpfulness."""
        print("💬 Evaluating response quality...")
        
        quality_scores = []
        
        test_inputs = [
            "add machine learning skill",
            "search for python developers in bangalore",
            "invalid request xyz abc",
            "remove java and add react as mandatory"
        ]
        
        for user_input in test_inputs:
            try:
                content = Content(data={
                    "request_type": "search_interaction",
                    "user_input": user_input,
                    "session_state": {"keywords": []}
                })
                
                result = await self.agent.execute(content)
                
                # Score based on various criteria
                score = 0
                
                # Success rate
                if result.data["success"]:
                    score += 2
                
                # Message quality
                message = result.data.get("message", "")
                if message and len(message) > 10:
                    score += 1
                
                # Appropriate error handling
                if not result.data["success"] and "error" in result.data:
                    score += 1
                
                # Suggestions for invalid requests
                if "invalid" in user_input.lower() and "suggestions" in result.data:
                    score += 1
                
                quality_scores.append(score / 5)  # Normalize to 0-1
                
            except Exception as e:
                quality_scores.append(0)
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        return {
            "average_quality_score": avg_quality,
            "quality_scores": quality_scores,
            "test_inputs": test_inputs
        }
    
    async def _evaluate_performance(self) -> Dict[str, Any]:
        """Evaluate system performance metrics."""
        print("⚡ Evaluating performance...")
        
        response_times = []
        
        # Test performance with various request types
        test_requests = [
            {"request_type": "health_check"},
            {"request_type": "search_interaction", "user_input": "add python", "session_state": {}},
            {"request_type": "candidate_search", "search_filters": {"keywords": ["Python"]}}
        ]
        
        for request_data in test_requests:
            start_time = time.time()
            
            try:
                content = Content(data=request_data)
                result = await self.agent.execute(content)
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
            except Exception as e:
                response_times.append(float('inf'))  # Mark as failed
        
        # Filter out failed requests
        valid_times = [t for t in response_times if t != float('inf')]
        
        return {
            "average_response_time": sum(valid_times) / len(valid_times) if valid_times else 0,
            "max_response_time": max(valid_times) if valid_times else 0,
            "min_response_time": min(valid_times) if valid_times else 0,
            "response_times": response_times,
            "success_rate": len(valid_times) / len(response_times)
        }
    
    async def _evaluate_system_health(self) -> Dict[str, Any]:
        """Evaluate overall system health."""
        print("🏥 Evaluating system health...")
        
        content = Content(data={"request_type": "health_check"})
        result = await self.agent.execute(content)
        
        health_score = 0
        max_score = 5
        
        if result.data["success"]:
            health_score += 1
        
        if result.data.get("database", {}).get("status") == "connected":
            health_score += 1
        
        if len(result.data.get("sub_agents", {})) > 0:
            health_score += 1
        
        if len(result.data.get("tools", [])) > 0:
            health_score += 1
        
        if result.data.get("status") == "healthy":
            health_score += 1
        
        return {
            "health_score": health_score / max_score,
            "health_details": result.data,
            "components_status": {
                "root_agent": result.data["success"],
                "database": result.data.get("database", {}).get("status") == "connected",
                "sub_agents": len(result.data.get("sub_agents", {})) > 0,
                "tools": len(result.data.get("tools", [])) > 0
            }
        }
    
    def _calculate_overall_score(self, intent_acc, response_qual, performance, health) -> float:
        """Calculate overall system score."""
        weights = {
            "intent_accuracy": 0.3,
            "response_quality": 0.25,
            "performance": 0.25,
            "system_health": 0.2
        }
        
        # Normalize performance score (faster is better)
        perf_score = min(1.0, 2.0 / max(performance["average_response_time"], 0.1))
        
        overall = (
            intent_acc["accuracy"] * weights["intent_accuracy"] +
            response_qual["average_quality_score"] * weights["response_quality"] +
            perf_score * weights["performance"] +
            health["health_score"] * weights["system_health"]
        )
        
        return overall
    
    def _save_results(self, results: Dict[str, Any]):
        """Save evaluation results to file."""
        results_file = Path(__file__).parent / "results" / f"eval_results_{int(time.time())}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📊 Results saved to: {results_file}")


async def main():
    """Main evaluation function."""
    evaluator = AgentEvaluator()
    results = await evaluator.run_evaluation()
    
    print("\n" + "="*50)
    print("📊 EVALUATION SUMMARY")
    print("="*50)
    print(f"🎯 Intent Recognition Accuracy: {results['intent_accuracy']['accuracy']:.2%}")
    print(f"💬 Response Quality Score: {results['response_quality']['average_quality_score']:.2f}/1.0")
    print(f"⚡ Average Response Time: {results['performance_metrics']['average_response_time']:.2f}s")
    print(f"🏥 System Health Score: {results['system_health']['health_score']:.2f}/1.0")
    print(f"🏆 Overall Score: {results['overall_score']:.2f}/1.0")
    print("="*50)
    
    # Recommendations
    if results['overall_score'] >= 0.8:
        print("✅ Excellent! System performing very well.")
    elif results['overall_score'] >= 0.6:
        print("⚠️ Good performance with room for improvement.")
    else:
        print("❌ System needs attention and optimization.")


if __name__ == "__main__":
    asyncio.run(main())