#!/usr/bin/env python3
"""Check task completion status for Telegram Bot Interface."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

# Constants
DEFAULT_TASKS_FILE = '.kiro/specs/telegram-bot-interface/tasks.md'
SEPARATOR = '=' * 60

# Regex patterns
PATTERNS = {
    'completed': r'^- \[x\] \d+\.',
    'optional': r'^- \[ \]\* \d+\.',
    'incomplete': r'^- \[ \] \d+\.'
}


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Check task completion status for Telegram Bot Interface'
    )
    parser.add_argument(
        '--file',
        default=DEFAULT_TASKS_FILE,
        help='Path to tasks.md file'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed task breakdown'
    )
    return parser.parse_args()


def read_tasks_file(filepath: str) -> str:
    """Read tasks file with error handling.
    
    Args:
        filepath: Path to the tasks file
        
    Returns:
        File content as string
        
    Raises:
        SystemExit: If file cannot be read
    """
    try:
        path = Path(filepath)
        if not path.exists():
            print(f"❌ Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        return path.read_text(encoding='utf-8')
    except PermissionError:
        print(f"❌ Error: Permission denied reading {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def count_tasks(content: str) -> Dict[str, int]:
    """Count different types of tasks.
    
    Args:
        content: Content of tasks file
        
    Returns:
        Dictionary with task counts
    """
    return {
        'completed': len(re.findall(PATTERNS['completed'], content, re.MULTILINE)),
        'optional': len(re.findall(PATTERNS['optional'], content, re.MULTILINE)),
        'incomplete': len(re.findall(PATTERNS['incomplete'], content, re.MULTILINE))
    }


def extract_incomplete_tasks(content: str) -> List[Dict[str, str]]:
    """Extract list of incomplete task descriptions.
    
    Args:
        content: Content of tasks file
        
    Returns:
        List of incomplete tasks with number and description
    """
    incomplete_tasks = []
    for line in content.split('\n'):
        match = re.match(r'^- \[ \] (\d+)\. (.+)', line)
        if match:
            incomplete_tasks.append({
                'number': match.group(1),
                'description': match.group(2)
            })
    return incomplete_tasks


def calculate_completion_percentage(counts: Dict[str, int]) -> float:
    """Calculate completion percentage.
    
    Args:
        counts: Dictionary with task counts
        
    Returns:
        Completion percentage
    """
    total = counts['completed'] + counts['incomplete']
    if total == 0:
        return 100.0
    return round((counts['completed'] / total) * 100, 2)


def print_json_status(counts: Dict[str, int]) -> None:
    """Print status in JSON format.
    
    Args:
        counts: Dictionary with task counts
    """
    output = {
        'completed': counts['completed'],
        'optional': counts['optional'],
        'incomplete': counts['incomplete'],
        'total': counts['completed'] + counts['incomplete'],
        'completion_percentage': calculate_completion_percentage(counts),
        'status': 'complete' if counts['incomplete'] == 0 else 'incomplete'
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def print_status(counts: Dict[str, int]) -> None:
    """Print formatted status report.
    
    Args:
        counts: Dictionary with task counts
    """
    print(SEPARATOR)
    print('СТАТУС ЗАДАЧ TELEGRAM BOT INTERFACE')
    print(SEPARATOR)
    print()
    print(f'✅ Завершено основных задач: {counts["completed"]}')
    print(f'⏭️  Опциональных задач (тесты): {counts["optional"]}')
    print(f'❌ Незавершенных обязательных задач: {counts["incomplete"]}')
    
    total = counts['completed'] + counts['incomplete']
    if total > 0:
        percentage = calculate_completion_percentage(counts)
        print(f'📊 Прогресс: {percentage}%')
    
    print()
    print(SEPARATOR)
    
    if counts['incomplete'] == 0:
        print('🎉 СТАТУС: ПОЛНОСТЬЮ ЗАВЕРШЕНО!')
        print('Все обязательные задачи выполнены.')
        print('Опциональные задачи (property-based тесты) можно')
        print('выполнить позже при необходимости.')
    else:
        print('⚠️  СТАТУС: ЕСТЬ НЕЗАВЕРШЕННЫЕ ЗАДАЧИ')
        print(f'Осталось выполнить: {counts["incomplete"]} задач(и)')
    
    print(SEPARATOR)


def print_verbose_status(counts: Dict[str, int], incomplete_tasks: List[Dict[str, str]]) -> None:
    """Print detailed status with incomplete task list.
    
    Args:
        counts: Dictionary with task counts
        incomplete_tasks: List of incomplete tasks
    """
    print_status(counts)
    
    if incomplete_tasks and counts['incomplete'] > 0:
        print()
        print('📋 НЕЗАВЕРШЕННЫЕ ЗАДАЧИ:')
        print('-' * 60)
        for task in incomplete_tasks:
            print(f"  {task['number']}. {task['description']}")
        print('-' * 60)


def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    # Read and parse tasks file
    content = read_tasks_file(args.file)
    counts = count_tasks(content)
    
    # Output results
    if args.json:
        print_json_status(counts)
    elif args.verbose:
        incomplete_tasks = extract_incomplete_tasks(content)
        print_verbose_status(counts, incomplete_tasks)
    else:
        print_status(counts)
    
    # Exit with appropriate code
    sys.exit(0 if counts['incomplete'] == 0 else 1)


if __name__ == '__main__':
    main()
