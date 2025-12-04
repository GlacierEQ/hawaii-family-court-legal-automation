#!/usr/bin/env python3
"""
Multi-Model FILEBOSS Integration

Intelligent AI model selection and routing for legal document tasks.
Supports fallback chains and performance monitoring.
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time

class ModelType(Enum):
    """AI model types"""
    GPT4 = "gpt-4"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    PERPLEXITY = "perplexity"
    LOCAL_LLAMA = "local-llama"

class TaskType(Enum):
    """Legal task types"""
    LEGAL_RESEARCH = "legal_research"
    DOCUMENT_GENERATION = "document_generation"
    LEGAL_ANALYSIS = "legal_analysis"
    EVIDENCE_REVIEW = "evidence_review"
    CITATION_CHECKING = "citation_checking"

@dataclass
class ModelProfile:
    """AI model capability profile"""
    model_type: ModelType
    strengths: List[TaskType]
    max_context: int  # tokens
    cost_per_1k_tokens: float
    avg_latency: float  # seconds
    reliability: float  # 0-1

@dataclass
class TaskResult:
    """Result from model execution"""
    success: bool
    output: Optional[str]
    model_used: ModelType
    execution_time: float
    tokens_used: int
    error: Optional[str] = None

class ModelRouter:
    """Intelligent model selection and routing"""
    
    def __init__(self):
        self.profiles = self._initialize_profiles()
        self.fallback_chains = self._initialize_fallbacks()
        self.performance_log: List[TaskResult] = []
        
    def _initialize_profiles(self) -> Dict[ModelType, ModelProfile]:
        """Initialize model capability profiles"""
        return {
            ModelType.GPT4: ModelProfile(
                model_type=ModelType.GPT4,
                strengths=[
                    TaskType.LEGAL_ANALYSIS,
                    TaskType.DOCUMENT_GENERATION,
                    TaskType.CITATION_CHECKING
                ],
                max_context=128000,
                cost_per_1k_tokens=0.03,
                avg_latency=2.5,
                reliability=0.95
            ),
            ModelType.CLAUDE_3_OPUS: ModelProfile(
                model_type=ModelType.CLAUDE_3_OPUS,
                strengths=[
                    TaskType.LEGAL_RESEARCH,
                    TaskType.DOCUMENT_GENERATION,
                    TaskType.LEGAL_ANALYSIS
                ],
                max_context=200000,
                cost_per_1k_tokens=0.015,
                avg_latency=3.0,
                reliability=0.93
            ),
            ModelType.CLAUDE_3_SONNET: ModelProfile(
                model_type=ModelType.CLAUDE_3_SONNET,
                strengths=[
                    TaskType.EVIDENCE_REVIEW,
                    TaskType.CITATION_CHECKING
                ],
                max_context=200000,
                cost_per_1k_tokens=0.003,
                avg_latency=1.5,
                reliability=0.90
            ),
            ModelType.PERPLEXITY: ModelProfile(
                model_type=ModelType.PERPLEXITY,
                strengths=[
                    TaskType.LEGAL_RESEARCH
                ],
                max_context=16000,
                cost_per_1k_tokens=0.001,
                avg_latency=2.0,
                reliability=0.88
            ),
            ModelType.LOCAL_LLAMA: ModelProfile(
                model_type=ModelType.LOCAL_LLAMA,
                strengths=[
                    TaskType.CITATION_CHECKING,
                    TaskType.EVIDENCE_REVIEW
                ],
                max_context=32000,
                cost_per_1k_tokens=0.0,  # Local, no API cost
                avg_latency=5.0,
                reliability=0.75
            )
        }
    
    def _initialize_fallbacks(self) -> Dict[TaskType, List[ModelType]]:
        """Initialize fallback chains for each task type"""
        return {
            TaskType.LEGAL_RESEARCH: [
                ModelType.PERPLEXITY,
                ModelType.CLAUDE_3_OPUS,
                ModelType.GPT4
            ],
            TaskType.DOCUMENT_GENERATION: [
                ModelType.CLAUDE_3_OPUS,
                ModelType.GPT4,
                ModelType.CLAUDE_3_SONNET
            ],
            TaskType.LEGAL_ANALYSIS: [
                ModelType.GPT4,
                ModelType.CLAUDE_3_OPUS,
                ModelType.CLAUDE_3_SONNET
            ],
            TaskType.EVIDENCE_REVIEW: [
                ModelType.CLAUDE_3_SONNET,
                ModelType.GPT4,
                ModelType.LOCAL_LLAMA
            ],
            TaskType.CITATION_CHECKING: [
                ModelType.CLAUDE_3_SONNET,
                ModelType.LOCAL_LLAMA,
                ModelType.GPT4
            ]
        }
    
    def select_model(self, 
                    task_type: str,
                    context_size: Optional[int] = None,
                    priority: str = "quality") -> ModelType:
        """Select best model for task
        
        Args:
            task_type: Type of task (string matching TaskType enum)
            context_size: Required context window size
            priority: "quality", "cost", or "speed"
            
        Returns:
            Selected ModelType
        """
        # Convert string to TaskType
        try:
            task = TaskType(task_type)
        except ValueError:
            # Default to legal analysis if unknown task
            task = TaskType.LEGAL_ANALYSIS
        
        # Get fallback chain for this task
        candidates = self.fallback_chains.get(task, [ModelType.GPT4])
        
        # Filter by context size if specified
        if context_size:
            candidates = [
                model for model in candidates
                if self.profiles[model].max_context >= context_size
            ]
        
        if not candidates:
            # Fallback to GPT-4 if no models meet requirements
            return ModelType.GPT4
        
        # Select based on priority
        if priority == "cost":
            return min(candidates, 
                      key=lambda m: self.profiles[m].cost_per_1k_tokens)
        elif priority == "speed":
            return min(candidates,
                      key=lambda m: self.profiles[m].avg_latency)
        else:  # quality
            return max(candidates,
                      key=lambda m: self.profiles[m].reliability)
    
    def execute_with_fallback(self,
                             task_type: TaskType,
                             task_fn: Callable,
                             *args,
                             **kwargs) -> TaskResult:
        """Execute task with automatic fallback on failure
        
        Args:
            task_type: Type of task to execute
            task_fn: Function that takes (model_type, *args, **kwargs)
            
        Returns:
            TaskResult with execution details
        """
        fallback_chain = self.fallback_chains.get(task_type, [ModelType.GPT4])
        
        for model_type in fallback_chain:
            start_time = time.time()
            
            try:
                output = task_fn(model_type, *args, **kwargs)
                execution_time = time.time() - start_time
                
                result = TaskResult(
                    success=True,
                    output=output,
                    model_used=model_type,
                    execution_time=execution_time,
                    tokens_used=0  # Would be populated by actual API
                )
                
                self.performance_log.append(result)
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log failure and try next model
                result = TaskResult(
                    success=False,
                    output=None,
                    model_used=model_type,
                    execution_time=execution_time,
                    tokens_used=0,
                    error=str(e)
                )
                self.performance_log.append(result)
                
                # If this was the last model, return error
                if model_type == fallback_chain[-1]:
                    return result
        
        # Should never reach here
        return TaskResult(
            success=False,
            output=None,
            model_used=fallback_chain[0],
            execution_time=0,
            tokens_used=0,
            error="No models available"
        )
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.performance_log:
            return {}
        
        total_tasks = len(self.performance_log)
        successful = sum(1 for r in self.performance_log if r.success)
        
        model_usage = {}
        for result in self.performance_log:
            model = result.model_used.value
            model_usage[model] = model_usage.get(model, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "success_rate": successful / total_tasks,
            "model_usage": model_usage,
            "avg_execution_time": sum(r.execution_time for r in self.performance_log) / total_tasks
        }

# Example usage
if __name__ == "__main__":
    router = ModelRouter()
    
    # Select model for legal research
    model = router.select_model("legal_research", priority="cost")
    print(f"Selected model for legal research: {model.value}")
    
    # Select model for document generation with large context
    model = router.select_model("document_generation", context_size=150000)
    print(f"Selected model for large document: {model.value}")
    
    # Example task execution with fallback
    def example_task(model_type: ModelType, prompt: str) -> str:
        """Example task function"""
        # Would call actual API here
        return f"Response from {model_type.value}: {prompt}"
    
    result = router.execute_with_fallback(
        TaskType.LEGAL_ANALYSIS,
        example_task,
        "Analyze this legal issue..."
    )
    
    print(f"\nTask result:")
    print(f"  Success: {result.success}")
    print(f"  Model used: {result.model_used.value}")
    print(f"  Output: {result.output}")
    
    # Get performance stats
    stats = router.get_performance_stats()
    print(f"\nPerformance stats: {stats}")
