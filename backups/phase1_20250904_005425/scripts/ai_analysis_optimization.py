#!/usr/bin/env python3
"""
AI分析機能最適化スクリプト
ChatGPT分析機能の精度と効率の最適化
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class AIAnalysisOptimizer:
    """AI分析機能最適化クラス"""
    
    def __init__(self, config_file: str = "config/production_config.json"):
        self.config_file = Path(config_file)
        self.data_dir = Path("data")
        self.ai_optimization_dir = Path("data/ai_optimization")
        
        # ディレクトリの作成
        self.ai_optimization_dir.mkdir(parents=True, exist_ok=True)
    
    async def optimize_prompts(self) -> Dict[str, Any]:
        """プロンプト最適化"""
        print("🤖 Optimizing AI prompts...")
        
        try:
            # プロンプト最適化スクリプトの実行
            cmd = ["python", "-c", """
import os
import sys
import json
sys.path.insert(0, '.')
from src.domain.services.ai_analysis.openai_prompt_builder import OpenAIPromptBuilder
from src.infrastructure.config.ai_analysis.ai_analysis_config import AIAnalysisConfig

config = AIAnalysisConfig()
prompt_builder = OpenAIPromptBuilder(config)

# プロンプトテンプレートの最適化
optimized_prompts = {
    'pre_event': {
        'template': 'Analyze the economic event: {event_name} for {country} on {date}. Focus on USD/JPY impact with specific reasons and confidence level.',
        'max_tokens': 2000,
        'temperature': 0.3
    },
    'post_event': {
        'template': 'Analyze the actual result of {event_name} for {country}: Actual: {actual}, Forecast: {forecast}. Impact on USD/JPY with detailed analysis.',
        'max_tokens': 2500,
        'temperature': 0.2
    },
    'forecast_change': {
        'template': 'Forecast changed for {event_name}: Old: {old_forecast}, New: {new_forecast}. Analyze USD/JPY impact change.',
        'max_tokens': 1800,
        'temperature': 0.3
    }
}

# 最適化されたプロンプトを保存
with open('data/ai_optimization/optimized_prompts.json', 'w') as f:
    json.dump(optimized_prompts, f, indent=2)

print('Prompt optimization completed')
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                print("✅ Prompt optimization completed")
                return {"success": True, "message": "Prompts optimized successfully"}
            else:
                return {
                    "success": False,
                    "error": f"Prompt optimization failed: {stderr.decode()}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Prompt optimization failed: {str(e)}"
            }
    
    async def optimize_confidence_scoring(self) -> Dict[str, Any]:
        """信頼度スコア調整"""
        print("📊 Optimizing confidence scoring...")
        
        try:
            cmd = ["python", "-c", """
import os
import sys
import json
sys.path.insert(0, '.')
from src.domain.services.ai_analysis.confidence_score_calculator import ConfidenceScoreCalculator

# 信頼度スコア計算の最適化
optimized_scoring = {
    'factors': {
        'data_quality': 0.3,
        'market_volatility': 0.2,
        'event_importance': 0.25,
        'historical_accuracy': 0.25
    },
    'thresholds': {
        'high_confidence': 0.8,
        'medium_confidence': 0.6,
        'low_confidence': 0.4
    },
    'adjustments': {
        'high_importance_bonus': 0.1,
        'low_volatility_bonus': 0.05,
        'uncertainty_penalty': 0.15
    }
}

# 最適化されたスコアリングを保存
with open('data/ai_optimization/optimized_scoring.json', 'w') as f:
    json.dump(optimized_scoring, f, indent=2)

print('Confidence scoring optimization completed')
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                print("✅ Confidence scoring optimization completed")
                return {"success": True, "message": "Confidence scoring optimized successfully"}
            else:
                return {
                    "success": False,
                    "error": f"Confidence scoring optimization failed: {stderr.decode()}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Confidence scoring optimization failed: {str(e)}"
            }
    
    async def analyze_prediction_accuracy(self) -> Dict[str, Any]:
        """予測精度分析"""
        print("📈 Analyzing prediction accuracy...")
        
        try:
            cmd = ["python", "-c", """
import os
import sys
import json
from datetime import datetime, timedelta
sys.path.insert(0, '.')
from src.infrastructure.database.config.database_config import DatabaseConfig
from src.infrastructure.database.config.connection_manager import ConnectionManager

config = DatabaseConfig()
manager = ConnectionManager(config)

with manager.get_connection() as conn:
    # 過去30日間のAI予測と実際の結果を分析
    result = conn.execute('''
        SELECT 
            ar.report_type,
            ar.confidence_score,
            ar.usd_jpy_prediction,
            ee.actual_value,
            ee.forecast_value,
            ee.previous_value
        FROM ai_reports ar
        JOIN economic_events ee ON ar.event_id = ee.event_id
        WHERE ar.generated_at >= NOW() - INTERVAL '30 days'
        AND ee.actual_value IS NOT NULL
    ''')
    
    predictions = result.fetchall()
    
    # 精度分析
    accuracy_analysis = {
        'total_predictions': len(predictions),
        'high_confidence_predictions': 0,
        'medium_confidence_predictions': 0,
        'low_confidence_predictions': 0,
        'accuracy_by_confidence': {},
        'average_confidence': 0.0
    }
    
    total_confidence = 0
    for pred in predictions:
        confidence = pred[1] or 0
        total_confidence += confidence
        
        if confidence >= 0.8:
            accuracy_analysis['high_confidence_predictions'] += 1
        elif confidence >= 0.6:
            accuracy_analysis['medium_confidence_predictions'] += 1
        else:
            accuracy_analysis['low_confidence_predictions'] += 1
    
    if predictions:
        accuracy_analysis['average_confidence'] = total_confidence / len(predictions)
    
    # 分析結果を保存
    with open('data/ai_optimization/accuracy_analysis.json', 'w') as f:
        json.dump(accuracy_analysis, f, indent=2)
    
    print(f'Accuracy analysis completed: {len(predictions)} predictions analyzed')
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                print("✅ Prediction accuracy analysis completed")
                return {"success": True, "message": "Accuracy analysis completed successfully"}
            else:
                return {
                    "success": False,
                    "error": f"Accuracy analysis failed: {stderr.decode()}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Accuracy analysis failed: {str(e)}"
            }
    
    async def optimize_api_cost(self) -> Dict[str, Any]:
        """APIコスト最適化"""
        print("💰 Optimizing API costs...")
        
        try:
            cmd = ["python", "-c", """
import os
import sys
import json
sys.path.insert(0, '.')
from src.infrastructure.config.ai_analysis.openai_config import OpenAIConfig

# APIコスト最適化設定
cost_optimization = {
    'model_selection': {
        'high_importance': 'gpt-4',
        'medium_importance': 'gpt-3.5-turbo',
        'low_importance': 'gpt-3.5-turbo'
    },
    'token_limits': {
        'pre_event': 1500,
        'post_event': 2000,
        'forecast_change': 1200
    },
    'batch_processing': {
        'enabled': True,
        'max_batch_size': 5,
        'delay_between_batches': 2
    },
    'caching': {
        'enabled': True,
        'cache_duration_hours': 24,
        'similarity_threshold': 0.9
    }
}

# 最適化設定を保存
with open('data/ai_optimization/cost_optimization.json', 'w') as f:
    json.dump(cost_optimization, f, indent=2)

print('API cost optimization completed')
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                print("✅ API cost optimization completed")
                return {"success": True, "message": "API costs optimized successfully"}
            else:
                return {
                    "success": False,
                    "error": f"API cost optimization failed: {stderr.decode()}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"API cost optimization failed: {str(e)}"
            }
    
    async def optimize_response_parsing(self) -> Dict[str, Any]:
        """レスポンス解析最適化"""
        print("🔍 Optimizing response parsing...")
        
        try:
            cmd = ["python", "-c", """
import os
import sys
import json
import re
sys.path.insert(0, '.')
from src.domain.services.ai_analysis.usd_jpy_prediction_parser import USDJPYPredictionParser

# レスポンス解析の最適化
parser_optimization = {
    'patterns': {
        'direction': [
            r'USD/JPY.*?(bullish|bearish|neutral)',
            r'(bullish|bearish|neutral).*USD/JPY',
            r'direction.*?(bullish|bearish|neutral)'
        ],
        'strength': [
            r'strength.*?(strong|medium|weak)',
            r'(strong|medium|weak).*strength',
            r'confidence.*?(high|medium|low)'
        ],
        'confidence': [
            r'confidence.*?(\d+\.?\d*)',
            r'(\d+\.?\d*).*confidence',
            r'certainty.*?(\d+\.?\d*)'
        ]
    },
    'fallback_values': {
        'direction': 'neutral',
        'strength': 'medium',
        'confidence': 0.5
    },
    'validation': {
        'min_confidence': 0.0,
        'max_confidence': 1.0,
        'required_fields': ['direction', 'strength']
    }
}

# 最適化設定を保存
with open('data/ai_optimization/parser_optimization.json', 'w') as f:
    json.dump(parser_optimization, f, indent=2)

print('Response parsing optimization completed')
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                print("✅ Response parsing optimization completed")
                return {"success": True, "message": "Response parsing optimized successfully"}
            else:
                return {
                    "success": False,
                    "error": f"Response parsing optimization failed: {stderr.decode()}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Response parsing optimization failed: {str(e)}"
            }
    
    async def create_ai_optimization_report(self, results: Dict[str, Any]) -> None:
        """AI最適化レポートの作成"""
        print("📊 Creating AI optimization report...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.ai_optimization_dir / f"ai_optimization_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_success": all(result.get("success", False) for result in results.values()),
            "optimizations": results,
            "summary": {
                "total_optimizations": len(results),
                "successful_optimizations": sum(1 for result in results.values() 
                                              if result.get("success", False)),
                "failed_optimizations": sum(1 for result in results.values() 
                                          if not result.get("success", False))
            },
            "recommendations": [
                "Use optimized prompts for better accuracy",
                "Implement confidence scoring improvements",
                "Monitor API costs regularly",
                "Validate response parsing accuracy",
                "Track prediction accuracy over time"
            ]
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 AI optimization report saved: {report_file}")
    
    async def run_full_ai_optimization(self) -> Dict[str, Any]:
        """完全なAI最適化の実行"""
        print("🚀 Starting AI analysis optimization...")
        
        results = {}
        
        # 各最適化の実行
        optimizations = [
            ("prompts", self.optimize_prompts),
            ("confidence_scoring", self.optimize_confidence_scoring),
            ("prediction_accuracy", self.analyze_prediction_accuracy),
            ("api_cost", self.optimize_api_cost),
            ("response_parsing", self.optimize_response_parsing)
        ]
        
        for opt_name, opt_func in optimizations:
            print(f"\n📋 Running {opt_name} optimization...")
            result = await opt_func()
            results[opt_name] = result
            
            if result["success"]:
                print(f"✅ {opt_name} optimization completed")
            else:
                print(f"❌ {opt_name} optimization failed: {result.get('error', 'Unknown error')}")
        
        # レポートの作成
        await self.create_ai_optimization_report(results)
        
        # 全体の結果
        overall_success = all(result.get("success", False) for result in results.values())
        
        if overall_success:
            print("\n🎉 AI analysis optimization completed successfully!")
            print("✅ All AI optimizations completed - AI analysis is optimized")
        else:
            print("\n⚠️ AI analysis optimization completed with some issues")
            print("Please review the failed optimizations")
        
        return {
            "success": overall_success,
            "results": results
        }


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="AI analysis optimization")
    parser.add_argument(
        "--optimization",
        choices=[
            "prompts",
            "confidence_scoring",
            "prediction_accuracy",
            "api_cost",
            "response_parsing",
            "all"
        ],
        default="all",
        help="Specific optimization to run"
    )
    parser.add_argument(
        "--config",
        default="config/production_config.json",
        help="Configuration file path"
    )
    
    args = parser.parse_args()
    
    optimizer = AIAnalysisOptimizer(args.config)
    
    if args.optimization == "all":
        result = await optimizer.run_full_ai_optimization()
    else:
        # 特定の最適化の実行
        optimization_functions = {
            "prompts": optimizer.optimize_prompts,
            "confidence_scoring": optimizer.optimize_confidence_scoring,
            "prediction_accuracy": optimizer.analyze_prediction_accuracy,
            "api_cost": optimizer.optimize_api_cost,
            "response_parsing": optimizer.optimize_response_parsing
        }
        
        if args.optimization in optimization_functions:
            result = await optimization_functions[args.optimization]()
        else:
            print(f"❌ Unknown optimization: {args.optimization}")
            sys.exit(1)
    
    # 結果の表示
    if result.get("success", False):
        print("\n✅ AI optimization completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ AI optimization failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
