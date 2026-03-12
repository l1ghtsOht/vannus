import { useRoomState } from '../context/RoomContext';

export default function useCostTracking() {
  const { cost } = useRoomState();

  return {
    total: cost.total,
    perModel: cost.perModel,
    modelCount: Object.keys(cost.perModel).length,
  };
}
