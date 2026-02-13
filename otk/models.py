"""
Model management utilities for Ollama
"""

import ollama
from typing import List, Dict, Optional
from datetime import datetime


class ModelManager:
    """
    Manage Ollama models - list, pull, delete, and get info
    
    Example:
        >>> manager = ModelManager()
        >>> models = manager.list_models()
        >>> manager.pull_model("llama2")
    """
    
    def __init__(self, host: Optional[str] = None):
        """
        Initialize the model manager
        
        Args:
            host: Optional custom host URL
        """
        self.client = ollama.Client(host=host) if host else ollama.Client()
    
    def list_models(self) -> List[Dict]:
        """
        List all available models
        
        Returns:
            List of model information dictionaries
        """
        response = self.client.list()
        models = []
        
        # Handle both dict and ListModelsResponse types
        if hasattr(response, 'models'):
            # ListModelsResponse object
            model_list = response.models
        elif isinstance(response, dict):
            # Dict response
            model_list = response.get('models', [])
        else:
            model_list = []
        
        for model in model_list:
            # Handle both dict and Model object types
            if hasattr(model, 'model'):
                # Model object with 'model' attribute as name
                model_name = model.model
                model_size = getattr(model, 'size', 0)
                model_modified = getattr(model, 'modified_at', '')
                model_details = getattr(model, 'details', {})
            elif isinstance(model, dict):
                # Dict with 'name' or 'model' key
                model_name = model.get('name') or model.get('model', 'unknown')
                model_size = model.get('size', 0)
                model_modified = model.get('modified_at', '')
                model_details = model.get('details', {})
            else:
                continue
            
            models.append({
                'name': model_name,
                'size': self._format_size(model_size),
                'modified': model_modified,
                'details': model_details
            })
        
        return models
    
    def pull_model(self, model_name: str, stream: bool = True) -> None:
        """
        Pull/download a model from Ollama library
        
        Args:
            model_name: Name of the model to pull
            stream: Whether to stream download progress
        """
        if stream:
            print(f"Pulling model: {model_name}")
            current_status = None
            
            for progress in self.client.pull(model_name, stream=True):
                status = progress.get('status', '')
                
                if status != current_status:
                    print(f"\n{status}", end='', flush=True)
                    current_status = status
                
                if 'completed' in progress and 'total' in progress:
                    completed = progress['completed']
                    total = progress['total']
                    percent = (completed / total * 100) if total > 0 else 0
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
            
            print("\n✓ Model pulled successfully!")
        else:
            self.client.pull(model_name)
    
    def delete_model(self, model_name: str) -> bool:
        """
        Delete a model
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete(model_name)
            return True
        except Exception as e:
            print(f"Error deleting model: {e}")
            return False
    
    def show_model_info(self, model_name: str) -> Dict:
        """
        Get detailed information about a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model information
        """
        try:
            response = self.client.show(model_name)
            return {
                'modelfile': response.get('modelfile', ''),
                'parameters': response.get('parameters', ''),
                'template': response.get('template', ''),
                'details': response.get('details', {}),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def model_exists(self, model_name: str) -> bool:
        """
        Check if a model exists locally
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model exists, False otherwise
        """
        models = self.list_models()
        return any(model['name'] == model_name for model in models)
    
    def get_model_size(self, model_name: str) -> Optional[str]:
        """
        Get the size of a model
        
        Args:
            model_name: Name of the model
            
        Returns:
            Formatted size string or None if not found
        """
        models = self.list_models()
        for model in models:
            if model['name'] == model_name:
                return model['size']
        return None
    
    @staticmethod
    def _format_size(bytes_size: int) -> str:
        """
        Format bytes to human-readable size
        
        Args:
            bytes_size: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
    
    def recommend_models(self) -> Dict[str, List[str]]:
        """
        Get recommended models for different use cases
        
        Returns:
            Dictionary of use cases and recommended models
        """
        return {
            'general_chat': ['llama2', 'mistral', 'phi'],
            'coding': ['codellama', 'deepseek-coder', 'starcoder2'],
            'fast_small': ['phi', 'tinyllama', 'orca-mini'],
            'powerful': ['llama2:70b', 'mixtral', 'solar'],
            'embeddings': ['nomic-embed-text', 'all-minilm'],
        }
