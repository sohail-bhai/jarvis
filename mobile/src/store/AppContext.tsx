import React, { createContext, useContext, useReducer, ReactNode, useCallback } from 'react';
import { Task, Device, ApprovalRequest, ActivityEntry, User } from '../services/types';

// State shape
interface AppState {
  user: User;
  tasks: Task[];
  devices: Device[];
  pendingApprovals: ApprovalRequest[];
  approvalCount: number;
  recentActivity: ActivityEntry[];
  isEmergencyStopped: boolean;
  isLoading: boolean;
  activeTaskId: string | null;
}

// Actions
type AppAction =
  | { type: 'SET_TASKS'; payload: Task[] }
  | { type: 'ADD_TASK'; payload: Task }
  | { type: 'UPDATE_TASK'; payload: Task }
  | { type: 'SET_DEVICES'; payload: Device[] }
  | { type: 'SET_APPROVALS'; payload: ApprovalRequest[] }
  | { type: 'SET_APPROVAL_COUNT'; payload: number }
  | { type: 'SET_ACTIVITY'; payload: ActivityEntry[] }
  | { type: 'SET_EMERGENCY_STOP'; payload: boolean }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ACTIVE_TASK'; payload: string | null };

const initialState: AppState = {
  user: {
    id: 'user-1',
    name: 'Rav',
    initials: 'R',
    workspace: 'Personal Workspace',
  },
  tasks: [],
  devices: [],
  pendingApprovals: [],
  approvalCount: 0,
  recentActivity: [],
  isEmergencyStopped: false,
  isLoading: false,
  activeTaskId: null,
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_TASKS':
      return { ...state, tasks: action.payload };
    case 'ADD_TASK':
      return { ...state, tasks: [action.payload, ...state.tasks] };
    case 'UPDATE_TASK':
      return {
        ...state,
        tasks: state.tasks.map(t => (t.id === action.payload.id ? action.payload : t)),
      };
    case 'SET_DEVICES':
      return { ...state, devices: action.payload };
    case 'SET_APPROVALS':
      return { ...state, pendingApprovals: action.payload };
    case 'SET_APPROVAL_COUNT':
      return { ...state, approvalCount: action.payload };
    case 'SET_ACTIVITY':
      return { ...state, recentActivity: action.payload };
    case 'SET_EMERGENCY_STOP':
      return { ...state, isEmergencyStopped: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ACTIVE_TASK':
      return { ...state, activeTaskId: action.payload };
    default:
      return state;
  }
}

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppState must be used within AppProvider');
  }
  return context;
}

export function useUser() {
  const { state } = useAppState();
  return state.user;
}
