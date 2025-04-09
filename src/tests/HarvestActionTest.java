
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
import java.util.Optional;

public class HarvestActionTest {


public PlayerAction Harvest_Resources(GameState game, int player, PlayerAction currentPlayerAction, PathFinding pf, UnitTypeTable a_utt, HashMap<Long, String> counterByFunction) {
    PlayerAction pa = new PlayerAction();
    List<Unit> playerUnits = game.getUnits();
    List<Unit> workers = playerUnits.stream()
        .filter(u -> u.getPlayer() == player && a_utt.getUnitType("Worker") != null && u.getType().equals(a_utt.getUnitType("Worker")))
        .toList();
    
    List<Unit> resources = playerUnits.stream()
        .filter(u -> u.getType().getName().equals("Resource"))
        .toList();
    
    List<Unit> assignedWorkers = new ArrayList<>();
    List<Unit> assignedResources = new ArrayList<>();
    
    for (Unit worker : workers) {
        if (worker.getResources() > 0 || !worker.getType().canHarvest()) {
            continue;
        }
        
        for (Unit resource : resources) {
            if (assignedResources.contains(resource) || assignedWorkers.contains(worker)) {
                continue;
            }
            
            if (pf.pathExists(worker, resource.getPosition(), game, new ResourceUsage())) {
                Harvest harvestAction = new Harvest();
                harvestAction.target = resource;
                harvestAction.base = worker.getType().getBase();
                harvestAction.pf = pf;
                
                if (!harvestAction.completed(game)) {
                    UnitAction ua = harvestAction.execute(game, new ResourceUsage());
                    if (ua != null && ua.getType() == UnitAction.TYPE_HARVEST) {
                        pa.addUnitAction(worker, ua);
                        assignedWorkers.add(worker);
                        assignedResources.add(resource);
                        break;
                    }
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
        }else if(score == 0) {
            System.out.println("0.0");

        }else {
            System.out.println(score);
        }


    } catch(Exception e) {

        System.err.println("-1.0");
    }
}

}

