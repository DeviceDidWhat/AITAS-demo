"""Diff formatter for visualizing code changes"""
import re
from typing import List, Tuple


class DiffFormatter:
    """Format code diffs with color and syntax highlighting"""

    @staticmethod
    def format_diff_text(text: str) -> List[Tuple[str, str]]:
        """
        Parse text and identify diff lines for colored display

        Returns:
            List of (line, style) tuples where style is 'add', 'remove', or 'normal'
        """
        lines = text.split('\n')
        formatted = []

        for line in lines:
            stripped = line.strip()

            # Check if line starts with diff markers
            if stripped.startswith('+ '):
                formatted.append((line, 'add'))
            elif stripped.startswith('- '):
                formatted.append((line, 'remove'))
            elif stripped.startswith('+') and len(stripped) > 1:
                # Handle +++ or just + at start
                formatted.append((line, 'add'))
            elif stripped.startswith('-') and len(stripped) > 1:
                # Handle --- or just - at start
                formatted.append((line, 'remove'))
            else:
                formatted.append((line, 'normal'))

        return formatted

    @staticmethod
    def extract_code_blocks(text: str) -> List[Tuple[str, bool]]:
        """
        Extract code blocks from text

        Returns:
            List of (content, is_code_block) tuples
        """
        blocks = []
        current_block = []
        in_code_block = False

        lines = text.split('\n')

        for line in lines:
            # Check for diff-style code (lines starting with +/-)
            if line.strip().startswith(('+', '-')) and not line.strip().startswith(('+++', '---')):
                in_code_block = True
                current_block.append(line)
            elif in_code_block and line.strip() and not line.strip().startswith(('+', '-', ' ')):
                # End of code block
                blocks.append(('\n'.join(current_block), True))
                current_block = [line]
                in_code_block = False
            else:
                current_block.append(line)

        # Add remaining block
        if current_block:
            blocks.append(('\n'.join(current_block), in_code_block))

        return blocks

    @staticmethod
    def highlight_changes_in_text(text: str) -> str:
        """
        Add Rich markup for color highlighting of diff lines

        Returns:
            Text with Rich color tags
        """
        lines = text.split('\n')
        highlighted = []

        for line in lines:
            stripped = line.lstrip()

            # Check for diff markers
            if stripped.startswith('+ '):
                # Green for additions
                highlighted.append(f"[green]{line}[/green]")
            elif stripped.startswith('- '):
                # Red for deletions
                highlighted.append(f"[red]{line}[/red]")
            elif stripped.startswith('+') and len(stripped) > 1 and not stripped.startswith('+++'):
                # Green for additions without space
                highlighted.append(f"[green]{line}[/green]")
            elif stripped.startswith('-') and len(stripped) > 1 and not stripped.startswith('---'):
                # Red for deletions without space
                highlighted.append(f"[red]{line}[/red]")
            else:
                # Normal text
                highlighted.append(line)

        return '\n'.join(highlighted)

    @staticmethod
    def is_diff_content(text: str) -> bool:
        """Check if text contains diff-style changes"""
        lines = text.split('\n')
        diff_count = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('+', '-')) and not stripped.startswith(('+++', '---', '++')):
                diff_count += 1

        # Consider it diff content if at least 10% of lines are diff markers
        return diff_count > 0 and (diff_count / max(len(lines), 1)) > 0.05

    @staticmethod
    def format_for_rich_panel(text: str) -> str:
        """
        Format text for Rich panel display with proper diff highlighting

        Args:
            text: Text potentially containing diff markers

        Returns:
            Text with Rich markup for colored display
        """
        if DiffFormatter.is_diff_content(text):
            return DiffFormatter.highlight_changes_in_text(text)
        return text

    @staticmethod
    def create_side_by_side_diff(old_code: str, new_code: str, context_lines: int = 3) -> str:
        """
        Create a side-by-side diff view (simplified)

        Args:
            old_code: Original code
            new_code: Modified code
            context_lines: Number of context lines around changes

        Returns:
            Formatted diff string
        """
        old_lines = old_code.split('\n')
        new_lines = new_code.split('\n')

        diff = []
        diff.append("[bold]Code Changes:[/bold]\n")

        max_len = max(len(old_lines), len(new_lines))

        for i in range(max_len):
            old_line = old_lines[i] if i < len(old_lines) else ""
            new_line = new_lines[i] if i < len(new_lines) else ""

            if old_line != new_line:
                if old_line:
                    diff.append(f"[red]- {old_line}[/red]")
                if new_line:
                    diff.append(f"[green]+ {new_line}[/green]")

        return '\n'.join(diff)
