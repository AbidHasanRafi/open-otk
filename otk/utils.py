"""
Utility functions for working with Ollama models
"""

from typing import List, Dict, Any, Optional
import re


def format_response(response: str, max_width: int = 80) -> str:
    """
    Format a response for better readability
    
    Args:
        response: The response text to format
        max_width: Maximum line width
        
    Returns:
        Formatted response
    """
    lines = response.split('\n')
    formatted_lines = []
    
    for line in lines:
        if len(line) <= max_width:
            formatted_lines.append(line)
        else:
            # Wrap long lines
            words = line.split()
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= max_width:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    formatted_lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                formatted_lines.append(' '.join(current_line))
    
    return '\n'.join(formatted_lines)


def estimate_tokens(text: str) -> int:
    """
    Rough estimation of token count
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    # Rough approximation: ~4 characters per token
    return len(text) // 4


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def create_prompt_template(
    template: str,
    variables: Dict[str, Any]
) -> str:
    """
    Fill in a prompt template with variables
    
    Args:
        template: Template string with {variable} placeholders
        variables: Dictionary of variable values
        
    Returns:
        Filled template
    """
    result = template
    for key, value in variables.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))
    return result


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown-formatted text
    
    Args:
        text: Text containing code blocks
        
    Returns:
        List of dictionaries with 'language' and 'code' keys
    """
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            'language': language or 'text',
            'code': code.strip()
        })
    
    return code_blocks


def clean_response(response: str) -> str:
    """
    Clean up common formatting issues in responses
    
    Args:
        response: Raw response text
        
    Returns:
        Cleaned response
    """
    # Remove excessive newlines
    response = re.sub(r'\n{3,}', '\n\n', response)
    
    # Remove trailing whitespace
    response = '\n'.join(line.rstrip() for line in response.split('\n'))
    
    # Remove leading/trailing whitespace
    response = response.strip()
    
    return response


def create_system_prompt(
    role: str,
    context: Optional[str] = None,
    constraints: Optional[List[str]] = None
) -> str:
    """
    Create a structured system prompt
    
    Args:
        role: The role for the AI (e.g., "helpful assistant", "Python expert")
        context: Optional context information
        constraints: Optional list of constraints/rules
        
    Returns:
        Formatted system prompt
    """
    prompt_parts = [f"You are a {role}."]
    
    if context:
        prompt_parts.append(f"\nContext: {context}")
    
    if constraints:
        prompt_parts.append("\nPlease follow these guidelines:")
        for i, constraint in enumerate(constraints, 1):
            prompt_parts.append(f"{i}. {constraint}")
    
    return '\n'.join(prompt_parts)


def batch_process(
    items: List[str],
    process_func,
    batch_size: int = 10,
    show_progress: bool = True
) -> List[Any]:
    """
    Process items in batches
    
    Args:
        items: List of items to process
        process_func: Function to apply to each item
        batch_size: Number of items per batch
        show_progress: Whether to show progress
        
    Returns:
        List of processed results
    """
    results = []
    total = len(items)
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        
        if show_progress:
            print(f"Processing batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}...")
        
        for item in batch:
            result = process_func(item)
            results.append(result)
    
    return results


def validate_model_name(model_name: str) -> bool:
    """
    Validate if a model name follows Ollama naming conventions
    
    Args:
        model_name: Model name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Basic validation: alphanumeric, hyphens, underscores, colons for tags
    pattern = r'^[a-zA-Z0-9_-]+(?::[a-zA-Z0-9_-]+)?$'
    return bool(re.match(pattern, model_name))


def format_chat_history(messages: List[Dict[str, str]]) -> str:
    """
    Format chat history for display
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Formatted chat history string
    """
    formatted = []
    
    for msg in messages:
        role = msg['role'].upper()
        content = msg['content']
        
        if role == 'SYSTEM':
            formatted.append(f"[SYSTEM]\n{content}\n")
        elif role == 'USER':
            formatted.append(f"👤 USER:\n{content}\n")
        elif role == 'ASSISTANT':
            formatted.append(f"🤖 ASSISTANT:\n{content}\n")
    
    return '\n'.join(formatted)
