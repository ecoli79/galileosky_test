class MoveRecord():
    def __init__(self, record_id: int, before_id: int = None, after_id: int = None):
      self.record_id = record_id
      self.before_id = before_id
      self.after_id = after_id
