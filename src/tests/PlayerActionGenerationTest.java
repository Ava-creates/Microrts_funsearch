package tests;

import ai.abstraction.Harvest;
import ai.abstraction.pathfinding.AStarPathFinding;
import rts.*;
import rts.units.Unit;
import rts.units.UnitTypeTable;
import java.util.List;

public class PlayerActionGenerationTest {
    public static void main(String args[]) {
        UnitTypeTable utt = new UnitTypeTable();
        MapGenerator mg = new MapGenerator(utt);
        PhysicalGameState pgs = mg.basesWorkers8x8(); // Changed map to ensure units are present       
        GameState gs = new GameState(pgs, utt);
        
        AStarPathFinding pf = new AStarPathFinding();
        
        for (Player p : pgs.getPlayers()) {
            List<Unit> units = pgs.getUnits();
            for (Unit unit : units) {
                if (unit.getPlayer() == p.getID()) {
                    Unit target = findClosestResource(unit, pgs);
                    Unit base = findBase(unit, pgs);
                    if (target != null && base != null) {
                        Harvest harvestAction = new Harvest(unit, target, base, pf);
                        System.out.println("Executing harvest action for unit: " + unit.getID());
                        harvestAction.execute(gs, new ResourceUsage());
                    }
                }
            }
        }
    }
    
    private static Unit findClosestResource(Unit unit, PhysicalGameState pgs) {
        Unit closest = null;
        double minDistance = Double.MAX_VALUE;
        for (Unit u : pgs.getUnits()) {
            if (u.getType().isResource) {
                double distance = Math.sqrt(Math.pow(unit.getX() - u.getX(), 2) + Math.pow(unit.getY() - u.getY(), 2));
                if (distance < minDistance) {
                    minDistance = distance;
                    closest = u;
                }
            }
        }
        return closest;
    }
    
    private static Unit findBase(Unit unit, PhysicalGameState pgs) {
        for (Unit u : pgs.getUnits()) {
            if (u.getType().isStockpile && u.getPlayer() == unit.getPlayer()) {
                return u;
            }
        }
        return null;
    }
}
