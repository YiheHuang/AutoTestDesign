"""状态机模型 - 用于白盒测试的状态转换建模"""

from typing import Optional
from pydantic import BaseModel, Field


class State(BaseModel):
    """状态"""
    id: str = Field(description="状态唯一标识")
    name: str = Field(description="状态名称")
    description: str = Field(default="", description="状态描述")
    is_initial: bool = Field(default=False, description="是否为初始状态")
    is_final: bool = Field(default=False, description="是否为终止状态")


class Transition(BaseModel):
    """状态转换"""
    id: str = Field(description="转换唯一标识")
    from_state: str = Field(description="起始状态ID")
    to_state: str = Field(description="目标状态ID")
    trigger: str = Field(description="触发条件/事件")
    guard: Optional[str] = Field(default=None, description="守卫条件")
    action: Optional[str] = Field(default=None, description="转换动作")


class StateMachine(BaseModel):
    """状态机"""
    id: str = Field(description="状态机唯一标识")
    name: str = Field(description="状态机名称")
    states: list[State] = Field(default_factory=list, description="状态列表")
    transitions: list[Transition] = Field(default_factory=list, description="转换列表")

    def get_initial_state(self) -> Optional[State]:
        """获取初始状态"""
        for s in self.states:
            if s.is_initial:
                return s
        return self.states[0] if self.states else None

    def get_state_by_id(self, state_id: str) -> Optional[State]:
        """根据ID获取状态"""
        for s in self.states:
            if s.id == state_id:
                return s
        return None

    def get_transitions_from(self, state_id: str) -> list[Transition]:
        """获取从某状态出发的所有转换"""
        return [t for t in self.transitions if t.from_state == state_id]

    def get_transitions_to(self, state_id: str) -> list[Transition]:
        """获取到达某状态的所有转换"""
        return [t for t in self.transitions if t.to_state == state_id]

    @property
    def state_count(self) -> int:
        return len(self.states)

    @property
    def transition_count(self) -> int:
        return len(self.transitions)
