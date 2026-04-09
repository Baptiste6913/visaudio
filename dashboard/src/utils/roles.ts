import { createContext, useContext } from "react";
import type { Role, StoreName } from "../types";

export interface RoleState {
  role: Role;
  store: StoreName | null;
  setRole: (r: Role) => void;
  setStore: (s: StoreName | null) => void;
}

export const RoleContext = createContext<RoleState>({
  role: "direction",
  store: null,
  setRole: () => {},
  setStore: () => {},
});

export const useRole = () => useContext(RoleContext);
