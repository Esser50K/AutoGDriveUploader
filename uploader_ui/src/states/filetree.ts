import { atom } from "recoil";

export type NodeState = {
  open: boolean;
};

export const nodesState = atom<{ [key: string]: NodeState }>({
  key: "nodesState",
  default: {},
});

export const selectedNodeState = atom({
  key: "selectedNodeState",
  default: "",
});
