# app/database/database.py
import os
from app.database.database_base import DatabaseBase
from app.database.schemas.sensors import Sensors
from app.database.schemas.curves import Curves
from app.database.schemas.curve_points import CurvePoints
from app.database.schemas.settings import Settings
from app.database.schemas.events import Events


class Database(DatabaseBase):
    def __init__(self, data_dir: str) -> None:
        super().__init__(data_dir, db_name="app.db")
        os.makedirs(self._data_dir, exist_ok=True)
        self.sensors = Sensors(data_dir)
        self.curves = Curves(data_dir)
        self.curve_points = CurvePoints(data_dir)
        self.settings = Settings(data_dir)
        self.events = Events(data_dir)

    def init(self) -> None:
        conn = self._connect()
        try:
            self.sensors._create_schema(conn)
            self.curves._create_schema(conn)
            self.curve_points._create_schema(conn)
            self.settings._create_schema(conn)
            self.events._create_schema(conn)
            conn.commit()
        finally:
            conn.close()