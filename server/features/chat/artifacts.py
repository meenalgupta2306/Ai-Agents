"""Artifact tracking and context building for chat sessions"""
from typing import List, Dict, Optional
from datetime import datetime


def extract_artifacts_from_history(session_messages: List[Dict]) -> List[Dict]:
    """
    Extract all artifacts from session message history.
    
    Args:
        session_messages: List of message dicts with role, content, timestamp, and optional metadata
        
    Returns:
        List of artifact dicts with type, path, filename, etc.
    """
    artifacts = []
    
    for msg in session_messages:
        # Check if message has metadata with tool_calls
        metadata = msg.get('metadata', {})
        tool_calls = metadata.get('tool_calls', [])
        
        for tool_call in tool_calls:
            artifact = tool_call.get('artifact')
            if artifact:
                # Add message timestamp for context
                artifact_with_context = artifact.copy()
                artifact_with_context['message_timestamp'] = msg.get('timestamp')
                artifact_with_context['tool_name'] = tool_call.get('name')
                artifacts.append(artifact_with_context)
    
    return artifacts


def build_artifact_context(artifacts: List[Dict]) -> str:
    """
    Build a hidden context message about generated artifacts.
    This message is injected into the conversation for the LLM to see,
    but is not shown to the user in the UI.
    
    Args:
        artifacts: List of artifact dicts from extract_artifacts_from_history()
        
    Returns:
        Formatted string describing all artifacts in the session
    """
    if not artifacts:
        return ""
    
    context = "📋 **Generated Artifacts in This Session:**\n\n"
    context += "The following files have been generated in this conversation. You can reference them when responding to the user.\n\n"
    
    for i, artifact in enumerate(artifacts, 1):
        artifact_type = artifact.get('type', 'unknown').replace('_', ' ').title()
        
        context += f"{i}. **{artifact_type}**\n"
        
        # Add title if available
        if 'title' in artifact:
            context += f"   - Title: \"{artifact['title']}\"\n"
        
        # Add file location
        if 'path' in artifact:
            context += f"   - Location: `{artifact['path']}`\n"
        
        if 'filename' in artifact:
            context += f"   - Filename: `{artifact['filename']}`\n"
        
        # Add format
        if 'format' in artifact:
            context += f"   - Format: {artifact['format'].upper()}\n"
        
        # Add creation time
        if 'created_at' in artifact:
            context += f"   - Created: {artifact['created_at']}\n"
        
        # Add query/prompt context
        if 'query' in artifact:
            context += f"   - Research Query: \"{artifact['query']}\"\n"
        elif 'prompt' in artifact:
            prompt_preview = artifact['prompt'][:60] + "..." if len(artifact['prompt']) > 60 else artifact['prompt']
            context += f"   - Prompt: \"{prompt_preview}\"\n"
        
        context += "\n"
    
    context += "**Instructions:**\n"
    context += "- When the user asks about 'that research', 'the report', or similar references, they are referring to the artifacts above\n"
    context += "- You can read file contents using appropriate tools if needed\n"
    context += "- Reference the file paths when creating follow-up content\n"
    
    return context.strip()


def extract_artifact_metadata(tool_name: str, result_text: str, tool_args: dict) -> Optional[Dict]:
    """
    Extract artifact metadata from tool execution results.
    This is used to automatically capture artifact info when tools are executed.
    
    Args:
        tool_name: Name of the tool that was executed
        result_text: Text result from the tool
        tool_args: Arguments passed to the tool
        
    Returns:
        Dict with artifact metadata or None if no artifact was generated
    """
    import re
    
    if tool_name == 'research_tool':
        # Parse: "LOCATION: documents/reports/final_report.html"
        match = re.search(r'LOCATION:\s*(.+\.(html|txt))', result_text)
        if match:
            file_path = match.group(1)
            file_format = match.group(2)
            
            return {
                'type': 'research_report',
                'format': file_format,
                'path': file_path,
                'filename': file_path.split('/')[-1],
                'query': tool_args.get('user_query', ''),
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
    
    elif tool_name == 'generate_image':
        # Extract image URL/path from result
        match = re.search(r'(documents/images/.+\.png)', result_text)
        if match:
            return {
                'type': 'image',
                'format': 'png',
                'path': match.group(1),
                'filename': match.group(1).split('/')[-1],
                'prompt': tool_args.get('prompt', ''),
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
    
    # Add more tool types as needed
    
    return None


def reconstruct_attachments_in_content(message: Dict) -> str:
    """
    Reconstruct message content with attachment links from metadata.
    
    Args:
        message: Message dict with role, content, and optional metadata
        
    Returns:
        Content string with attachment links appended
    """
    content = message.get('content', '')
    metadata = message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    
    if not attachments:
        return content
    
    # Add attachment links
    attachment_links = '\n'.join([
        f"[{att.get('filename', 'Attachment')}]({att.get('url', '')})"
        for att in attachments
    ])
    
    return f"{content}\n\n**Attached Files:**\n{attachment_links}"
