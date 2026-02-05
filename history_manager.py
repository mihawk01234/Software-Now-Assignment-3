class HistoryManager:
    """
    Manages Undo/Redo using stacks.
    Stores copies of images so we can restore older versions.
    """

    def __init__(self, max_states=15):
        self._undo_stack = []
        self._redo_stack = []
        self._max_states = max_states

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()

    def push(self, img):
        if img is None:
            return
        self._undo_stack.append(img.copy())
        if len(self._undo_stack) > self._max_states:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def can_undo(self):
        return len(self._undo_stack) > 0

    def can_redo(self):
        return len(self._redo_stack) > 0

    def undo(self, current_img):
        if not self.can_undo():
            return None
        self._redo_stack.append(current_img.copy())
        return self._undo_stack.pop()

    def redo(self, current_img):
        if not self.can_redo():
            return None
        self._undo_stack.append(current_img.copy())
        return self._redo_stack.pop()
