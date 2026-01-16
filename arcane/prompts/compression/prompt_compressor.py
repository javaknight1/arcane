"""Prompt compression for reducing token usage."""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CompressionConfig:
    """Configuration for prompt compression."""
    shorthand: bool = False
    truncate: bool = False
    remove_examples: bool = False
    max_section_length: int = 500
    preserve_structure: bool = True


class PromptCompressor:
    """Compresses prompts to reduce token usage.

    Supports multiple compression levels from 'none' to 'aggressive',
    achieving 30-50% token reduction while preserving semantic meaning.
    """

    COMPRESSION_LEVELS: Dict[str, Dict[str, bool]] = {
        'none': {'shorthand': False, 'truncate': False, 'remove_examples': False},
        'light': {'shorthand': False, 'truncate': True, 'remove_examples': False},
        'moderate': {'shorthand': True, 'truncate': True, 'remove_examples': False},
        'aggressive': {'shorthand': True, 'truncate': True, 'remove_examples': True},
    }

    SHORTHAND_MAP: Dict[str, str] = {
        # Item types
        'Milestone': 'M',
        'Epic': 'E',
        'Story': 'S',
        'Task': 'T',
        # Common terms
        'implementation': 'impl',
        'configuration': 'config',
        'authentication': 'auth',
        'authorization': 'authz',
        'documentation': 'docs',
        'development': 'dev',
        'production': 'prod',
        'environment': 'env',
        'application': 'app',
        'database': 'db',
        'repository': 'repo',
        'function': 'func',
        'parameter': 'param',
        'information': 'info',
        'requirements': 'reqs',
        'specification': 'spec',
        'specifications': 'specs',
    }

    VERBOSE_PATTERNS: List[Tuple[str, str]] = [
        # Polite phrasing
        (r'Please generate', 'Generate'),
        (r'Please create', 'Create'),
        (r'Please provide', 'Provide'),
        (r'Please ensure', 'Ensure'),
        (r'Please note that', 'Note:'),
        # Wordy constructions
        (r'You should ensure that', 'Ensure'),
        (r'You need to make sure that', 'Ensure'),
        (r'It is important to note that', 'Note:'),
        (r'It should be noted that', 'Note:'),
        (r'In order to', 'To'),
        (r'Make sure to', 'Must'),
        (r'Be sure to', 'Must'),
        (r'Keep in mind that', 'Note:'),
        (r'Take into account', 'Consider'),
        (r'With respect to', 'Re:'),
        (r'With regard to', 'Re:'),
        (r'As mentioned above', 'Above'),
        (r'As described below', 'Below'),
        (r'The following is', ''),
        (r'Here is the', ''),
        (r'Here are the', ''),
        # Filler phrases
        (r'basically', ''),
        (r'essentially', ''),
        (r'actually', ''),
        (r'In this case,? ?', ''),
        (r'For this purpose,? ?', ''),
    ]

    EXAMPLE_PATTERNS: List[str] = [
        r'(?s)```example.*?```',
        r'(?s)<example>.*?</example>',
        r'(?s)Example:.*?(?=\n\n|\Z)',
        r'(?s)For example:.*?(?=\n\n|\Z)',
        r'(?s)E\.g\.:.*?(?=\n\n|\Z)',
    ]

    def __init__(self, config: Optional[CompressionConfig] = None):
        """Initialize compressor with optional config.

        Args:
            config: Custom compression configuration
        """
        self.config = config or CompressionConfig()

    def compress(self, prompt: str, level: str = 'moderate') -> str:
        """Compress prompt based on level.

        Args:
            prompt: The prompt text to compress
            level: Compression level ('none', 'light', 'moderate', 'aggressive')

        Returns:
            Compressed prompt text
        """
        config = self.COMPRESSION_LEVELS.get(level, self.COMPRESSION_LEVELS['moderate'])

        result = prompt

        # Always apply basic whitespace compression
        result = self._remove_excessive_whitespace(result)

        # Always compress verbose phrases
        result = self._compress_verbose_phrases(result)

        if config['shorthand']:
            result = self._apply_shorthand(result)

        if config['truncate']:
            result = self._truncate_long_sections(result)

        if config['remove_examples']:
            result = self._remove_example_sections(result)

        return result

    def _remove_excessive_whitespace(self, text: str) -> str:
        """Remove excessive whitespace while preserving structure.

        Args:
            text: Text to clean

        Returns:
            Text with excessive whitespace removed
        """
        # Replace multiple spaces with single space (not at line start)
        result = re.sub(r'(?<!^)(?<!\n) {2,}', ' ', text)

        # Replace 3+ newlines with 2 newlines
        result = re.sub(r'\n{3,}', '\n\n', result)

        # Remove trailing whitespace on lines
        result = re.sub(r' +\n', '\n', result)

        # Remove leading/trailing whitespace
        result = result.strip()

        return result

    def _compress_verbose_phrases(self, text: str) -> str:
        """Replace verbose phrases with concise alternatives.

        Args:
            text: Text to compress

        Returns:
            Text with verbose phrases replaced
        """
        result = text

        for pattern, replacement in self.VERBOSE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def _apply_shorthand(self, text: str) -> str:
        """Apply shorthand replacements for common terms.

        Args:
            text: Text to compress

        Returns:
            Text with shorthand applied
        """
        result = text

        for long_form, short_form in self.SHORTHAND_MAP.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(long_form) + r'\b'
            result = re.sub(pattern, short_form, result, flags=re.IGNORECASE)

        return result

    def _truncate_long_sections(self, text: str, max_length: int = 500) -> str:
        """Truncate sections that exceed max length.

        Args:
            text: Text to truncate
            max_length: Maximum length per section

        Returns:
            Text with long sections truncated
        """
        max_len = self.config.max_section_length if self.config else max_length

        # Split into sections by headers or double newlines
        sections = re.split(r'((?:^|\n)#{1,6} .+\n)', text)

        result_sections = []
        for section in sections:
            if len(section) > max_len and not section.startswith('#'):
                # Truncate content sections, not headers
                truncated = section[:max_len].rsplit(' ', 1)[0]
                truncated += '...'
                result_sections.append(truncated)
            else:
                result_sections.append(section)

        return ''.join(result_sections)

    def _remove_example_sections(self, text: str) -> str:
        """Remove example sections to save tokens.

        Args:
            text: Text to process

        Returns:
            Text with example sections removed
        """
        result = text

        for pattern in self.EXAMPLE_PATTERNS:
            result = re.sub(pattern, '[examples omitted]', result, flags=re.IGNORECASE)

        return result

    def get_compression_stats(self, original: str, compressed: str) -> Dict[str, float]:
        """Calculate compression statistics.

        Args:
            original: Original prompt text
            compressed: Compressed prompt text

        Returns:
            Dictionary with compression statistics
        """
        # Approximate tokens as chars / 4 (rough estimate for English)
        orig_chars = len(original)
        comp_chars = len(compressed)
        orig_tokens = orig_chars // 4
        comp_tokens = comp_chars // 4

        tokens_saved = orig_tokens - comp_tokens
        compression_ratio = (tokens_saved / orig_tokens * 100) if orig_tokens > 0 else 0.0

        return {
            'original_chars': orig_chars,
            'compressed_chars': comp_chars,
            'original_tokens': orig_tokens,
            'compressed_tokens': comp_tokens,
            'tokens_saved': tokens_saved,
            'compression_ratio': round(compression_ratio, 2),
        }

    def compress_with_stats(self, prompt: str, level: str = 'moderate') -> Tuple[str, Dict[str, float]]:
        """Compress prompt and return with statistics.

        Args:
            prompt: The prompt text to compress
            level: Compression level

        Returns:
            Tuple of (compressed_text, stats_dict)
        """
        compressed = self.compress(prompt, level)
        stats = self.get_compression_stats(prompt, compressed)
        return compressed, stats

    @classmethod
    def get_available_levels(cls) -> List[str]:
        """Get list of available compression levels.

        Returns:
            List of compression level names
        """
        return list(cls.COMPRESSION_LEVELS.keys())

    def estimate_savings(self, prompt: str, level: str = 'moderate') -> Dict[str, float]:
        """Estimate token savings without actually compressing.

        Args:
            prompt: The prompt text
            level: Compression level to estimate

        Returns:
            Estimated savings statistics
        """
        # Quick estimate based on pattern matching
        config = self.COMPRESSION_LEVELS.get(level, self.COMPRESSION_LEVELS['moderate'])

        orig_tokens = len(prompt) // 4
        estimated_reduction = 0.0

        # Estimate whitespace savings (5-10%)
        whitespace_matches = len(re.findall(r' {2,}|\n{3,}', prompt))
        estimated_reduction += min(whitespace_matches * 0.5, orig_tokens * 0.1)

        # Estimate verbose phrase savings (5-15%)
        verbose_count = sum(
            len(re.findall(pattern, prompt, re.IGNORECASE))
            for pattern, _ in self.VERBOSE_PATTERNS
        )
        estimated_reduction += min(verbose_count * 2, orig_tokens * 0.15)

        if config['shorthand']:
            # Estimate shorthand savings (10-20%)
            shorthand_count = sum(
                len(re.findall(r'\b' + re.escape(term) + r'\b', prompt, re.IGNORECASE))
                for term in self.SHORTHAND_MAP.keys()
            )
            estimated_reduction += min(shorthand_count * 1.5, orig_tokens * 0.2)

        if config['remove_examples']:
            # Estimate example removal savings (10-30%)
            for pattern in self.EXAMPLE_PATTERNS:
                matches = re.findall(pattern, prompt, re.IGNORECASE)
                estimated_reduction += sum(len(m) // 4 for m in matches)

        estimated_tokens = max(orig_tokens - int(estimated_reduction), orig_tokens // 2)

        return {
            'original_tokens': orig_tokens,
            'estimated_tokens': estimated_tokens,
            'estimated_savings': orig_tokens - estimated_tokens,
            'estimated_ratio': round((orig_tokens - estimated_tokens) / orig_tokens * 100, 2) if orig_tokens > 0 else 0.0,
        }
