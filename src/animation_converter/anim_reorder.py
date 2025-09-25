from typing import Dict, List, Set, Tuple

from petscii import PetsciiScreen


def calc_shared_chars(screen1: PetsciiScreen, screen2: PetsciiScreen) -> int:
    """
    Calculate number of shared characters between two screens.

    Args:
        screen1: First PetsciiScreen object
        screen2: Second PetsciiScreen object

    Returns:
        Number of characters that appear in both screens
    """
    chars1: Set = set(screen1.charset)
    chars2: Set = set(screen2.charset)
    return len(chars1.intersection(chars2))


def reorder_screens_by_similarity(screens: List[PetsciiScreen]) -> List[PetsciiScreen]:
    """
    Reorders a list of PetsciiScreen objects so that screens with the most
    characters in common are adjacent to each other.

    Args:
        screens: List of PetsciiScreen objects

    Returns:
        List of PetsciiScreen objects in optimized order
    """
    if len(screens) <= 2:
        return screens

    # Build adjacency matrix of shared character counts
    n = len(screens)
    similarity_matrix: Dict[Tuple[int, int], int] = {}

    # Initialize matrix including self-connections
    for i in range(n):
        for j in range(n):
            if i == j:
                # A screen shares all its characters with itself
                similarity_matrix[(i, j)] = len(set(screens[i].charset))
            else:
                shared = calc_shared_chars(screens[i], screens[j])
                similarity_matrix[(i, j)] = shared

    # Start with screen that has most shared chars with others (excluding self)
    total_shared = [
        sum(similarity_matrix[(i, j)] for j in range(n) if i != j) for i in range(n)
    ]
    current = max(range(n), key=lambda i: total_shared[i])

    # Build path greedily choosing next screen with most shared chars
    used = {current}
    result = [screens[current]]

    while len(result) < len(screens):
        # Find unused screen with most shared chars with current screen
        next_screen = max(
            (i for i in range(n) if i not in used),
            key=lambda i: similarity_matrix[(current, i)],
        )
        result.append(screens[next_screen])
        used.add(next_screen)
        current = next_screen

    return result


def get_charset_changes(screens: List[PetsciiScreen]) -> List[Tuple[int, int, int]]:
    """
    Helper function to analyze number of charset changes between screens.

    Args:
        screens: List of PetsciiScreen objects

    Returns:
        List of tuples containing (prev_screen_idx, next_screen_idx, num_changes)
        where num_changes is the number of new characters needed when transitioning
        from prev_screen to next_screen
    """
    changes = []
    for i in range(len(screens) - 1):
        prev_chars = set(screens[i].charset)
        next_chars = set(screens[i + 1].charset)
        num_changes = len(next_chars - prev_chars)
        changes.append((i, i + 1, num_changes))
    return changes
