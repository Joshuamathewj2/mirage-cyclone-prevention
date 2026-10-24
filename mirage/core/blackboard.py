import json
from datetime import datetime
from typing import Any, Dict, List, Optional
try:
    import redis
except ImportError:  # optional infrastructure extra
    redis = None
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:  # optional infrastructure extra
    create_engine = sessionmaker = None
from mirage.models.entities import Cyclone, Shelter, Resource, Route, Task, Decision, Approval

class Blackboard:
    def __init__(self, redis_url: Optional[str] = None, db_url: Optional[str] = None):
        self.redis_mem = {}
        self.redis = None
        self.use_redis = False
        if redis_url and redis:
            try:
                candidate = redis.from_url(redis_url, decode_responses=True)
                candidate.ping()
                self.redis = candidate
                self.use_redis = True
            except Exception:
                print("Redis unavailable; using in-memory blackboard.")
        self.engine = None
        self.Session = None
        self.use_db = False
        if db_url and create_engine:
            try:
                self.engine = create_engine(db_url)
                self.Session = sessionmaker(bind=self.engine)
                self.use_db = True
            except Exception:
                print("Database unavailable; persistence disabled.")
        self.sim_id = "sim_default"

    def set_simulation_id(self, sim_id: str):
        self.sim_id = sim_id

    # Redis Helpers
    def _key(self, region: str, entity_id: str) -> str:
        return f"mirage:{self.sim_id}:blackboard:{region}:{entity_id}"

    def update_cyclone(self, data: Dict[str, Any]):
        key = self._key("incidents", "cyclone_01")
        if self.use_redis:
            self.redis.set(key, json.dumps(data))
            self.redis.xadd(f"mirage:{self.sim_id}:streams:cyclone", {"data": json.dumps(data)})
        else:
            self.redis_mem[key] = json.dumps(data)

    def get_cyclone(self) -> Optional[Dict[str, Any]]:
        key = self._key("incidents", "cyclone_01")
        val = self.redis.get(key) if self.use_redis else self.redis_mem.get(key)
        return json.loads(val) if val else None

    def update_shelters(self, updates: List[Dict[str, Any]]):
        for update in updates:
            key = self._key("shelters", update["id"])
            if self.use_redis:
                current = self.redis.get(key)
                if current:
                    shelter_data = json.loads(current)
                    shelter_data.update(update)
                    self.redis.set(key, json.dumps(shelter_data))
                else:
                    self.redis.set(key, json.dumps(update))
            else:
                current = self.redis_mem.get(key)
                if current:
                    shelter_data = json.loads(current)
                    shelter_data.update(update)
                    self.redis_mem[key] = json.dumps(shelter_data)
                else:
                    self.redis_mem[key] = json.dumps(update)
        
        if self.use_redis:
            self.redis.xadd(f"mirage:{self.sim_id}:streams:shelter", {"updates": json.dumps(updates)})

    def get_shelters(self) -> List[Dict[str, Any]]:
        if self.use_redis:
            keys = self.redis.keys(f"mirage:{self.sim_id}:blackboard:shelters:*")
            return [json.loads(self.redis.get(k)) for k in keys]
        else:
            prefix = f"mirage:{self.sim_id}:blackboard:shelters:"
            return [json.loads(v) for k, v in self.redis_mem.items() if k.startswith(prefix)]

    def update_resources(self, updates: List[Dict[str, Any]]):
        for update in updates:
            key = self._key("resources", update["id"])
            if self.use_redis:
                current = self.redis.get(key)
                if current:
                    res_data = json.loads(current)
                    res_data.update(update)
                    self.redis.set(key, json.dumps(res_data))
                else:
                    self.redis.set(key, json.dumps(update))
            else:
                current = self.redis_mem.get(key)
                if current:
                    res_data = json.loads(current)
                    res_data.update(update)
                    self.redis_mem[key] = json.dumps(res_data)
                else:
                    self.redis_mem[key] = json.dumps(update)
                    
        if self.use_redis:
            self.redis.xadd(f"mirage:{self.sim_id}:streams:resource", {"updates": json.dumps(updates)})

    def get_resources(self) -> List[Dict[str, Any]]:
        if self.use_redis:
            keys = self.redis.keys(f"mirage:{self.sim_id}:blackboard:resources:*")
            return [json.loads(self.redis.get(k)) for k in keys]
        else:
            prefix = f"mirage:{self.sim_id}:blackboard:resources:"
            return [json.loads(v) for k, v in self.redis_mem.items() if k.startswith(prefix)]

    def update_infra(self, updates: List[Dict[str, Any]]):
        for update in updates:
            key = self._key("routes", update["id"])
            if self.use_redis:
                current = self.redis.get(key)
                if current:
                    route_data = json.loads(current)
                    route_data.update(update)
                    self.redis.set(key, json.dumps(route_data))
                else:
                    self.redis.set(key, json.dumps(update))
            else:
                current = self.redis_mem.get(key)
                if current:
                    route_data = json.loads(current)
                    route_data.update(update)
                    self.redis_mem[key] = json.dumps(route_data)
                else:
                    self.redis_mem[key] = json.dumps(update)
                    
        if self.use_redis:
            self.redis.xadd(f"mirage:{self.sim_id}:streams:routes", {"updates": json.dumps(updates)})

    def set_pop_movement(self, movement: Dict[str, Any]):
        key = f"mirage:{self.sim_id}:pop_movement"
        if self.use_redis:
            self.redis.set(key, json.dumps(movement))
        else:
            self.redis_mem[key] = json.dumps(movement)

    def get_pop_movement(self) -> Dict[str, Any]:
        key = f"mirage:{self.sim_id}:pop_movement"
        val = self.redis.get(key) if self.use_redis else self.redis_mem.get(key)
        return json.loads(val) if val else {}

    def publish_event(self, channel: str, payload: Dict[str, Any]):
        if self.use_redis:
            self.redis.xadd(f"mirage:{self.sim_id}:streams:{channel}", {"payload": json.dumps(payload)})

    def get_approvals(self) -> List[Dict[str, Any]]:
        if self.use_redis:
            keys = self.redis.keys(f"mirage:{self.sim_id}:blackboard:approvals:*")
            return [json.loads(self.redis.get(k)) for k in keys]
        else:
            prefix = f"mirage:{self.sim_id}:blackboard:approvals:"
            return [json.loads(v) for k, v in self.redis_mem.items() if k.startswith(prefix)]

    def _json_serialize(self, data: Any) -> str:
        def default(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        return json.dumps(data, default=default)

    def update_approval(self, req_data: Dict[str, Any]):
        key = self._key("approvals", req_data["id"])
        serialized = self._json_serialize(req_data)
        if self.use_redis:
            self.redis.set(key, serialized)
        else:
            self.redis_mem[key] = serialized

    def update_allocation_plan(self, plan_data: Dict[str, Any]):
        key = self._key("allocations", plan_data["plan_id"])
        serialized = self._json_serialize(plan_data)
        if self.use_redis:
            self.redis.set(key, serialized)
        else:
            self.redis_mem[key] = serialized

    def get_allocations(self) -> List[Dict[str, Any]]:
        if self.use_redis:
            keys = self.redis.keys(f"mirage:{self.sim_id}:blackboard:allocations:*")
            return [json.loads(self.redis.get(k)) for k in keys]
        else:
            prefix = f"mirage:{self.sim_id}:blackboard:allocations:"
            return [json.loads(v) for k, v in self.redis_mem.items() if k.startswith(prefix)]
