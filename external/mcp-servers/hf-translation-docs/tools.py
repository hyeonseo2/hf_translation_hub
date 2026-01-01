"""MCP tool endpoints for HuggingFace translation documentation."""

from __future__ import annotations
from typing import Any, Dict

from services import (
    get_project_configuration,
    search_translation_files_data,
    get_file_content_data,
    generate_translation_prompt_data,
    validate_translation_data,
    save_translation_result_data,
)


def get_project_config(project: str, toolCallId: str = "") -> Dict[str, Any]:
    """
    Get project-specific configuration and settings.
    
    MCP endpoint: translation_get_project_config

    Args:
        project: The name of the project to get the configuration for.
        toolCallId: The ID of the tool call.

    Returns:
        A dictionary containing the project configuration.

    Raises:
        Exception: If the project configuration cannot be retrieved.
    """
    try:
        return {
            "status": "success",
            "data": get_project_configuration(project)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "PROJECT_CONFIG_ERROR",
                "message": str(e),
                "details": {"project": project}
            }
        }


def search_translation_files(
    project: str,
    target_language: str,
    max_files: int = 10,
    toolCallId: str = "",
) -> Dict[str, Any]:
    """
    Search for files that need translation.

    MCP endpoint: translation_search_files

    Args:
        project: The name of the project to search for files in.
        target_language: The target language to search for files in.
        max_files: The maximum number of files to return.
        toolCallId: The ID of the tool call.
    Returns:
        A dictionary containing the search results.

    Raises:
        Exception: If the files cannot be searched for.
    """
    try:
        data = search_translation_files_data(project, target_language, max_files)
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "SEARCH_FILES_ERROR",
                "message": str(e),
                "details": {
                    "project": project,
                    "target_language": target_language,
                    "max_files": max_files
                }
            }
        }


def get_file_content(
    project: str,
    file_path: str,
    include_metadata: bool = True,
    toolCallId: str = "",
) -> Dict[str, Any]:
    """
    Get file content for translation.
    
    MCP endpoint: translation_get_file_content

    Args:
        project: The name of the project to get the file content for.
        file_path: The path of the file to get the content for.
        include_metadata: Whether to include metadata in the response.
        toolCallId: The ID of the tool call.

    Returns:
        A dictionary containing the file content.

    Raises:
        Exception: If the file content cannot be retrieved.
    """
    try:
        data = get_file_content_data(project, file_path, include_metadata)
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "FILE_CONTENT_ERROR",
                "message": str(e),
                "details": {
                    "project": project,
                    "file_path": file_path
                }
            }
        }


def generate_translation_prompt(
    target_language: str,
    content: str,
    additional_instruction: str = "",
    project: str = "transformers",
    file_path: str = "",
    toolCallId: str = "",
) -> Dict[str, Any]:
    """
    Generate translation prompt for content.
    
    MCP endpoint: translation_generate_prompt

    Args:
        target_language: The target language to generate the prompt for.
        content: The content to generate the prompt for.
        additional_instruction: Additional instruction to generate the prompt.
        project: The name of the project to generate the prompt for.
        file_path: The path of the file to generate the prompt for.
        toolCallId: The ID of the tool call.

    Returns:
        A dictionary containing the generated prompt.

    Raises:
        Exception: If the prompt cannot be generated.
    """
    try:
        data = generate_translation_prompt_data(
            target_language, content, additional_instruction, project, file_path
        )
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "PROMPT_GENERATION_ERROR",
                "message": str(e),
                "details": {
                    "target_language": target_language,
                    "content_length": len(content),
                    "project": project,
                    "file_path": file_path
                }
            }
        }


def validate_translation(
    original_content: str,
    translated_content: str,
    target_language: str,
    file_path: str = "",
    toolCallId: str = "",
) -> Dict[str, Any]:
    """
    Validate translated content for quality and formatting.
    
    MCP endpoint: translation_validate

    Args:
        original_content: The original content to validate.
        translated_content: The translated content to validate.
        target_language: The target language to validate the content for.
        file_path: The path of the file to validate the content for.
        toolCallId: The ID of the tool call.

    Returns:
        A dictionary containing the validation results.

    Raises:
        Exception: If the content cannot be validated.
    """
    try:
        data = validate_translation_data(
            original_content, translated_content, target_language, file_path
        )
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": {
                    "original_content_length": len(original_content),
                    "translated_content_length": len(translated_content),
                    "target_language": target_language,
                    "file_path": file_path
                }
            }
        }


def save_translation_result(
    project: str,
    original_file_path: str,
    translated_content: str,
    target_language: str,
    metadata: Dict[str, Any] = None,
    toolCallId: str = "",
) -> Dict[str, Any]:
    """
    Save translation result to file system.
    
    MCP endpoint: translation_save_result

    Args:
        project: The name of the project to save the translation result for.
        original_file_path: The path of the original file to save the translation result for.
        translated_content: The translated content to save the translation result for.
        target_language: The target language to save the translation result for.
        metadata: The metadata to save the translation result for.
        toolCallId: The ID of the tool call.

    Returns:
        A dictionary containing the saved translation result.

    Raises:
        Exception: If the translation result cannot be saved.
    """
    try:
        data = save_translation_result_data(
            project, original_file_path, translated_content, target_language, metadata
        )
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "SAVE_RESULT_ERROR",
                "message": str(e),
                "details": {
                    "project": project,
                    "original_file_path": original_file_path,
                    "target_language": target_language,
                    "content_length": len(translated_content)
                }
            }
        }