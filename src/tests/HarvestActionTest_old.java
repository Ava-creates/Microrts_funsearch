package tests;

import ai.synthesis.dslForScriptGenerator.DSLParametersConcrete.QuantityParam;
import ai.synthesis.dslForScriptGenerator.DSLParametersConcrete.TypeConcrete;
import ai.abstraction.pathfinding.BFSPathFinding;
import ai.abstraction.pathfinding.PathFinding;
import ai.abstraction.Harvest;
import ai.synthesis.dslForScriptGenerator.DSLCommand.DSLBasicAction.HarvestBasic;
import rts.*;
import rts.units.Unit;
import rts.units.UnitType;
import rts.units.UnitTypeTable;

import java.util.List;
import java.util.HashMap;

public class HarvestActionTest {

  public PlayerAction Harvest_Resources(GameState game, int player, PlayerAction currentPlayerAction,
                                       PathFinding pf, UnitTypeTable a_utt, HashMap<Long, String> counterByFunction) {
        PlayerAction pa = new PlayerAction();
        ResourceUsage ru = new ResourceUsage();

        List<Unit> units = game.getUnits();
        for (Unit u : units) {
            if (u.getPlayer() != player) continue;
            if (!u.isIdle(game)) continue;

            String lastFunction = counterByFunction.getOrDefault(u.getID(), "");

            Unit closestResource = null;
            Unit closestBase = null;
            int closestResourceDist = Integer.MAX_VALUE;
            int closestBaseDist = Integer.MAX_VALUE;

            for (Unit target : units) {
                if (target.getType().isResource) {
                    int d = Math.abs(u.getX() - target.getX()) + Math.abs(u.getY() - target.getY());
                    if (d < closestResourceDist) {
                        closestResourceDist = d;
                        closestResource = target;
                    }
                } else if (target.getType().isStockpile && target.getPlayer() == player) {
                    int d = Math.abs(u.getX() - target.getX()) + Math.abs(u.getY() - target.getY());
                    if (d < closestBaseDist) {
                        closestBaseDist = d;
                        closestBase = target;
                    }
                }
            }

            if (closestResource != null && closestBase != null) {
                Harvest harvestAction = new Harvest(u, closestResource, closestBase, pf);
                if (!harvestAction.completed(game)) {
                    UnitAction ua = harvestAction.execute(game, ru);
                    if (ua != null && game.isUnitActionAllowed(u, ua)) {
                        pa.addUnitAction(u, ua);
                        ru.merge(ua.resourceUsage(u, game.getPhysicalGameState()));
                        counterByFunction.put(u.getID(), "Harvest");
                    }
                }
            }
        }

        return pa;
    }

  
    public static void main(String[] args)
     {
    UnitTypeTable utt = new UnitTypeTable();
    try {
        PhysicalGameState pgs = PhysicalGameState.load("/Users/avanitiwari/Desktop/MicroRTS/maps/8x8/basesWorkers8x8B.xml", utt);
        GameState gs = new GameState(pgs, utt);
        int player = 0;

        BFSPathFinding pf = new BFSPathFinding();
   
        HashMap<Long, String> counterByFunction = new HashMap<>();
        HarvestActionTest testRunner = new HarvestActionTest();
        boolean functionRan = false;
        int resourcesBefore = gs.getPlayer(0).getResources();

        int cycles = 1000;
        PlayerAction pa = testRunner.Harvest_Resources(gs, player, new PlayerAction(), pf, utt, counterByFunction);
        gs.issueSafe(pa);
        functionRan = true;
        int score =0;
        for (int i = 0; i < cycles && !gs.gameover(); i++) {
            try {
                gs.cycle();
            } catch (Exception e) {
                System.err.println("-1.0");
            }
        }
        int resourcesAfter = gs.getPlayer(0).getResources();

        score = resourcesAfter - resourcesBefore;
        if (!functionRan) {
            System.out.println("-1.0");
        } else if(score == 0) {
            System.out.println("0.0");
        
        } else {
            System.out.println(score);
        }
       

    } catch(Exception e) {

        System.err.println("-1.0");
    }
}

}
