from collections.abc import Collection, Sequence
import requests
import numpy as np
import random
import os
from groq import Groq
import csv
import subprocess
import os

os.environ['GROQ_API_KEY'] = "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"
client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )

context ="""Generate a function which has the following function signature:

public PlayerAction Harvest_Resources(GameState game, int player, PlayerAction currentPlayerAction, PathFinding pf, UnitTypeTable a_utt, HashMap<Long, String> counterByFunction)

Below classes are available to be used to construct Harvest_Resources function:

ai.abstraction.AbstractAction; - This is an abstract class which is inherited by all the actions like Attack, Build, Harvest, Idle, Move, etc.
public abstract class AbstractAction {
    Unit unit;
    public AbstractAction(Unit a_unit) {} - Constructor
    public Unit getUnit() {} - Getter for Unit
    public void setUnit(Unit u) {} - Setter for Unit
    public abstract boolean completed(GameState pgs);
    public UnitAction execute(GameState pgs){}
    public abstract UnitAction execute(GameState pgs, ResourceUsage ru);
}

ai.abstraction.Harvest; - This class extends the AbstractAction class.
public class Harvest extends AbstractAction  {
    Unit target;
    Unit base;
    PathFinding pf;
    public Harvest(Unit u, Unit a_target, Unit a_base, PathFinding a_pf) {} - Constructor
    public Unit getTarget() {} - Getter for target
    public Unit getBase() {} - Getter for base
    public boolean completed(GameState gs) { } - Returns true if the units don’t have the base, given that the unit has resources. If it doesn’t have resources, then it will return true if the units don’t have the target.
    public UnitAction execute(GameState gs, ResourceUsage ru) {} - Returns a UnitAction of TYPE_HARVEST with a direction (DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT) if it can find a path to any adjacent viable position. The direction is determined by the x and y coordinates of the base and target units.
}

ai.abstraction.pathfinding.PathFinding; - This is an abstract class which is inherited by classes like AStarPathFinding, BFSPathFinding, FloodFillPathfinding, GreedyPathfinding, etc.
public abstract class PathFinding {
    public abstract boolean pathExists(Unit start, int targetpos, GameState gs, ResourceUsage ru);
    public abstract boolean pathToPositionInRangeExists(Unit start, int targetpos, int range, GameState gs, ResourceUsage ru);
    public abstract UnitAction findPath(Unit start, int targetpos, GameState gs, ResourceUsage ru);
    public abstract UnitAction findPathToPositionInRange(Unit start, int targetpos, int range, GameState gs, ResourceUsage ru);
    public abstract UnitAction findPathToAdjacentPosition(Unit start, int targetpos, GameState gs, ResourceUsage ru);
    public String toString() {} - Returns the simple name of the class
}

rts.GameState; - This class represents a fully-observable game state
public class GameState {
    public static final boolean REPORT_ILLEGAL_ACTIONS = false;
    static Random r = new Random();         // only used if the action conflict resolution strategy is set to random
    protected int unitCancelationCounter = 0;  // only used if the action conflict resolution strategy is set to alternating
    protected int time = 0;
    protected PhysicalGameState pgs;
    protected HashMap<Unit,UnitActionAssignment> unitActions = new LinkedHashMap<>();
    protected UnitTypeTable utt;
    private static final int NUM_VECTOR_OBSERVATION_FEATURE_MAPS = 6;
    public GameState(PhysicalGameState a_pgs, UnitTypeTable a_utt) {} - Initializes the GameState
    public int getTime() {} - Current game timestep (frames since beginning)
    public void removeUnit(Unit u) {}
    public Player getPlayer(int ID) {}
    public Unit getUnit(long ID) {}
    public List<Unit> getUnits() {}
    public HashMap<Unit,UnitActionAssignment> getUnitActions() {} - Returns a map with the units and the actions assigned to them
    public UnitTypeTable getUnitTypeTable() {}
    public UnitAction getUnitAction(Unit u) { }
    public UnitActionAssignment getActionAssignment(Unit u) {} - Returns the action assigned to a unit
    public boolean isComplete() {} - Indicates whether all units owned by the players have a valid action or not
    public int winner() {}
    public boolean gameover() {}
    public PhysicalGameState getPhysicalGameState() {}
     public boolean free(int x, int y) {} - Returns true if there is no unit in the specified position and no unit is executing an action that will use that position
    public boolean[][] getAllFree() {} - Returns a boolean array with true if there is no unit in the specified position and no unit is executing an action that will use that position
    public boolean observable(int x, int y) {} - Returns whether the cell is observable. For fully observable game states, all the cells are observable.
    public boolean issue(PlayerAction pa) {} - Issues a player action. Returns “true" if any action different from NONE was issued
    public boolean issueSafe(PlayerAction pa) {}  - Issues a player action, with additional checks for validity. This function is slower than "issue", and should not be used internally by any AI. It is used externally in the main loop to verify that the actions proposed by an AI are valid, before sending them to the game.
    public boolean canExecuteAnyAction(int pID) {} - Indicates whether a player can issue an action in this state
    public boolean isUnitActionAllowed(Unit u, UnitAction ua) {} - This function checks whether the intended unit action  has any conflicts with some other action. It assumes that the UnitAction ua is valid (i.e. one of the actions that the unit can potentially execute)
    public List<PlayerAction> getPlayerActionsSingleUnit(Unit unit) {}
    public List<PlayerAction> getPlayerActions(int playerID) {}
    public int getNextChangeTime() {} - Returns the time the next unit action will complete, or current time if a player can act
    public boolean cycle() {} - Runs a game cycle, execution all assigned actions, returns whether the game was over
    public void forceExecuteAllActions() {} - Forces the execution of all assigned actions
    public GameState clone() {}
    public GameState cloneIssue(PlayerAction pa) {} - This method does a quick clone, that shares the same PGS, but different unit assignments
    public GameState cloneChangingUTT(UnitTypeTable new_utt) {} - Clone this game state, replacing the active UnitTypeTable
    public ResourceUsage getResourceUsage() {} - Returns the resources being used for all actions issued in current cycle
    public boolean integrityCheck() {} - Verifies integrity: if an action was assigned to non-existing unit or two actions were assigned to the same unit, integrity is violated
    public void dumpActionAssignments() {} - Shows UnitActionAssignments on the terminal
       public int [][][] getVectorObservation(final int player){} - Constructs a vector observation for a player
}

rts.PhysicalGameState; - This class represents the physical game state (the actual 'map') of a microRTS game
public class PhysicalGameState {
    public static final int TERRAIN_NONE = 0; - Indicates a free tile
    public static final int TERRAIN_WALL = 1; - Indicates a blocked tile

    int width = 8;
    int height = 8;
    int terrain[];
    List<Player> players = new ArrayList<>();
    List<Unit> units = new LinkedList<>();
    public static PhysicalGameState load(String fileName, UnitTypeTable utt) throws Exception {} - Constructs the game state map from a XML
    public PhysicalGameState(int a_width, int a_height) {} - Creates a new game state map with the informed width and height. Initializes an empty terrain.
    PhysicalGameState(int a_width, int a_height, int t[]) {} - Creates a new game state map with the informed width and height. Initializes with the received terrain.
    public int getWidth() {}
    public int getHeight() {}
    public void setWidth(int w) {} - Sets a new width. This do not change the terrain array, remember to change that when you change the map width or height
    public void setHeight(int h) {} - Sets a new height. This do not change the terrain array, remember to change that when you change the map width or height
    public int getTerrain(int x, int y) {} - Returns what is on a given position of the terrain
    public void setTerrain(int x, int y, int v) {} - Puts an entity in a given position of the terrain
    public void setTerrain(int t[]) {} - Sets the whole terrain
    public void addPlayer(Player p) {} - Adds a player
    public void addUnit(Unit newUnit) throws IllegalArgumentException {} - Adds a new Unit to the map if its position is free. Throws IllegalArgumentException if the new unit's position is already occupied
    public void removeUnit(Unit u) {} - Removes a unit from the map
    public List<Unit> getUnits() {} - Returns the list of units in the map
    public List<Player> getPlayers() {} - Returns a list of players
    public Player getPlayer(int pID) {} - Returns a player given its ID
    public Unit getUnit(long ID) {} - Returns a Unit given its ID or null if not found
    public Unit getUnitAt(int x, int y) {} - Returns the Unit at a given coordinate or null if no unit is present
    public Collection<Unit> getUnitsAround(int x, int y, int squareRange) {} - Returns the units within a squared area centered in the given coordinates
    public Collection<Unit> getUnitsAround(int x, int y, int width, int height) {} - Returns units within a rectangular area centered in the given coordinates
    public Collection<Unit> getUnitsInRectangle(int x, int y, int width, int height) {} - Returns units within a rectangle with the given top-left vertex and dimensions. Tests for x <= unitX < x+width && y <= unitY < y+height. Notice that the test is inclusive in top and left but exclusive on bottom and right
    public int winner() {} - Returns the winner of the game, given the unit counts or -1 if the game is not over
    boolean gameover() {} - Returns whether the game is over. The game is over when a player has zero units

    public PhysicalGameState clone() {}
    public PhysicalGameState cloneKeepingUnits() {} - Clone the physical game state, but does not clone the units The terrain is shared amongst all instances, since it never changes
    public PhysicalGameState cloneIncludingTerrain() {} - Clones the physical game state, including its terrain    
    public String toString() {}
    public boolean equivalents(PhysicalGameState pgs) {} - This function tests if two PhysicalGameStates are identical
    public boolean equivalentsIncludingTerrain(PhysicalGameState pgs) {} - This function tests if two PhysicalGameStates are identical, including their terrain
    public boolean[][] getAllFree() {} - Returns an array with true if the given position has
     PhysicalGameState.TERRAIN_NONE
    private String compressTerrain() {} - Create a compressed String representation of the terrain vector. The terrain vector is an array of Integers, whose elements only assume 0 and 1 as possible values. This method compresses the terrain vector by counting the number of consecutive occurrences of a value and appending this to a String. Since 0 and 1 may appear in the counter, 0 is replaced by A and 1 is replaced by B. For example, the String 00000011110000000000 is transformed into A6B4A10. This method is useful when the terrain composes part of a message, to be shared between client and server.
    private static int[] uncompressTerrain(String t) {} - Create an uncompressed int array from a compressed String representation of the terrain
    public void toxml(XMLWriter w) {} - Writes a XML representation of the map
    public void toxml(XMLWriter w, boolean includeConstants, boolean compressTerrain) {}
    public void toJSON(Writer w) throws Exception {} - Writes a JSON representation of this map
    public void toJSON(Writer w, boolean includeConstants, boolean compressTerrain) throws Exception {}
    public static PhysicalGameState fromXML(Element e, UnitTypeTable utt) throws Exception {} - Constructs a map from XM
    public static PhysicalGameState fromJSON(JsonObject o, UnitTypeTable utt) {} - Constructs a map from JSON
    private static int[] getTerrainFromUnknownString(String terrainString, int size) {} - Transforms a compressed or uncompressed String representation of the terrain into an integer array
    public void resetAllUnitsHP() {} - Reset all units HP to their base value
}

rts.PlayerAction; - This class stores a collection of pairs of (Unit, UnitAction)
public class PlayerAction {
    List<Pair<Unit,UnitAction>> actions = new LinkedList<>();
    ResourceUsage r = new ResourceUsage(); - Represents the resources used by the player action
    public PlayerAction() {}
    public boolean equals(Object o) {}
    public boolean isEmpty() {} - Returns whether there are no player actions
    public boolean hasNonNoneActions() {} - Returns whether the player has assigned any action different than UnitAction.TYPE_NONE to any of its units
    public int hasNamNoneActions() {} - Returns the number of actions different than
    UnitAction.TYPE_NONE
    public ResourceUsage getResourceUsage() {} - Returns the usage of resources
    public void setResourceUsage(ResourceUsage a_r) {} - Sets the resource usage
    public void addUnitAction(Unit u, UnitAction a) {} - Adds a new {@link UnitAction} to a given Unit
    public void removeUnitAction(Unit u, UnitAction a) {} - Removes a pair of Unit and UnitAction from the list
    public PlayerAction merge(PlayerAction a) {} - Merges this with another PlayerAction
    public List<Pair<Unit,UnitAction>> getActions() {} - Returns a list of pairs of units and UnitActions
    public UnitAction getAction(Unit u) {} - Searches for the unit in the collection and returns the respective UnitAction
    public List<PlayerAction> cartesianProduct(List<UnitAction> lu, Unit u, GameState s) {}
    public boolean consistentWith(ResourceUsage u, GameState gs) {} - Returns whether this PlayerAction is consistent with a given ResourceUsage and a GameState
    public void fillWithNones(GameState s, int pID, int duration) {} - Assign "none" to all the units that need an action and do not have one for the specified duration
    public boolean integrityCheck() {} - Returns true if this object passes the integrity check. It fails if the unit is being assigned an action from a player that does not owns it
    public void clear() {} - Resets the PlayerAction
    public static PlayerAction fromVectorAction(int[][] actions, GameState gs, UnitTypeTable utt, int currentPlayer, int maxAttackRadius) {} - Creates a full assignment of actions to inactive units for a given player from a vector-based action representation. actions is a vector representation of actions. Outer dimension is for the list of actions/units, i.e. actions[i] gives us the vector representation for the i^th unit that we are assigning an action to. currentPlayer is the Player whom we are processing actions for. maxAttackRadius should be 2*a + 1, where a is the maximum attack range over all units.
}

rts.ResourceUsage; - This class tracks the resources being used
public class ResourceUsage {
    List<Integer> positionsUsed = new LinkedList<>();
    int[] resourcesUsed = new int[2];
    public ResourceUsage() {}
    public boolean consistentWith(ResourceUsage anotherUsage, GameState gs) {} - Returns whether this instance is consistent with another ResourceUsage in a given game state. Resource usages are consistent if they respect the players' resource amount and don't have conflicting uses
    public List<Integer> getPositionsUsed() {} - Returns the list with used resource positions
    public int getResourcesUsed(int player) {} - Returns the amount of resources used by the player
    public ResourceUsage mergeIntoNew(ResourceUsage other) {} - Merges this and another instance of ResourceUsage into a new one
    public void merge(ResourceUsage other) {} - Merges another instance of ResourceUsage into this one
    public ResourceUsage clone() {}
}

rts.UnitAction; - This class represents all kinds of actions that a unit can take
public class UnitAction {
    public static Random r = new Random();  // only used for non-deterministic events
    public static final int TYPE_NONE = 0; - The 'no-op' action
    public static final int TYPE_MOVE = 1; - Action of moving
    public static final int TYPE_HARVEST = 2; - Action of harvesting
    public static final int TYPE_RETURN = 3; - Action of return to base with resource
    public static final int TYPE_PRODUCE = 4; - Action of produce a unit
    public static final int TYPE_ATTACK_LOCATION = 5; - Action of attacking a location
    public static final int NUMBER_OF_ACTION_TYPES = 6; - Total number of action types
    public static String actionName[] = {
        "wait", "move", "harvest", "return", "produce", "attack_location"
    };
    public static final int DIRECTION_NONE = -1; - Direction of 'standing still'
    public static final int DIRECTION_UP = 0; - Alias for up
    public static final int DIRECTION_RIGHT = 1; - Alias for right
    public static final int DIRECTION_DOWN = 2; - Alias for down
    public static final int DIRECTION_LEFT = 3; - Alias for left
    public static final int DIRECTION_OFFSET_X[] = {0, 1, 0, -1}; - The offset caused by each direction of movement in X Indexes correspond to the constants used in this class
    public static final int DIRECTION_OFFSET_Y[] = {-1, 0, 1, 0}; - The offset caused by each direction of movement in y Indexes correspond to the constants used in this class
    public static final String DIRECTION_NAMES[] = {"up", "right", "down", "left"}; - Direction names. Indexes correspond to the constants used in this class
    int type = TYPE_NONE;-- Type of this UnitAction
    int parameter = DIRECTION_NONE; - used for both "direction" and "duration"
    int x = 0, y = 0; - X and Y coordinates of an attack-location action
    UnitType unitType; - UnitType associated with a 'produce' action
    ResourceUsage r_cache; - Amount of resources associated with this action
    public UnitAction(int a_type) {} - Creates an action with specified type
        public UnitAction(int a_type, int a_direction) {} - Creates an action with type and direction
    public UnitAction(int a_type, int a_direction, UnitType a_unit_type) {} - Creates an action with type, direction and unit type
    public UnitAction(int a_type, int a_x, int a_y) {} - Creates a unit action with coordinates
    public UnitAction(UnitAction other) {} - Copies the parameters of other unit action
    public boolean equals(Object o) {}
    public int hashCode() {
        int hash = this.type;
        hash = 19 * hash + this.parameter;
        hash = 19 * hash + this.x;
        hash = 19 * hash + this.y;
        hash = 19 * hash + Objects.hashCode(this.unitType);
        return hash;
    }
    public int getType() {} - Returns the type associated with this action
    public UnitType getUnitType() {} - Returns the UnitType associated with this action
    public ResourceUsage resourceUsage(Unit u, PhysicalGameState pgs) {} - Returns the ResourceUsage associated with this action, given a Unit and a PhysicalGameState
    public int ETA(Unit u) {} - Returns the estimated time of conclusion of this action The Unit parameter is necessary for actions of TYPE_MOVE, TYPE_ATTACK_LOCATION and TYPE_RETURN. In other cases it can be null
    public void execute(Unit u, GameState s) {} - Effects this action in the game state. If the action is related to a unit, changes it position accordingly
    public String getActionName() {} - Returns the name of this action
    public int getDirection() {} - Returns the direction associated with this action
    public int getLocationX() {} - Returns the X coordinate associated with this action
    public int getLocationY() {} - Returns the Y coordinate associated with this action
         public UnitAction(Element e, UnitTypeTable utt) {} - Creates a UnitAction from a XML element
        public static UnitAction fromVectorAction(int[] action, UnitTypeTable utt, GameState gs, Unit u, int maxAttackRange) {} - Creates a UnitAction from an action array. Expects [x_coordinate(x)  y_coordinate(y), a_t(6), p_move(4), p_harvest(4), p_return(4), p_produce_direction(4), p_produce_unit_type(z), p_attack_location_x_coordinate(x), p_attack_location_y_coordinate(y), frameskip(n)]. maxAttackRange should be 2*a + 1, where a is the maximum attack range over all units.
    public static void getValidActionArray(Unit u, GameState gs, UnitTypeTable utt, int[] mask, int maxAttackRange, int idxOffset) {}
}

rts.units.Unit; - This class represents an instance of any unit in the game.
public class Unit implements Serializable {
    UnitType type; - The type of this unit (worker, ranged, barracks, etc.)
    public static long next_ID = 0; - Indicates the ID to assign to a new unit. It is incremented when the constructor without explicit ID is used
    long ID; - The unique identifier of this unit
    int player; - Owner ID
    int x, y; - Coordinates
    int resources; - Resources this unit is carrying
    int hitpoints = 0; - Unit hit points
    public Unit(long a_ID, int a_player, UnitType a_type, int a_x, int a_y, int a_resources) {} - Constructs a unit, specifying with all parameters, including the ID. next_ID gets ID+1 if ID >= next_ID.
public Unit(int a_player, UnitType a_type, int a_x, int a_y, int a_resources) {} - Creates a unit without specifying its ID. It is automatically assigned from next_ID, which is incremented.
    public Unit(int a_player, UnitType a_type, int a_x, int a_y) {} - Creates a unit without specifying resources, which receive zero
    public Unit(Unit other) {} - Copies the attributes from other unit
    public int getPlayer() {} - Returns the owner ID
    public UnitType getType() {} - Returns the type
    public void setType(UnitType a_type) {} - Sets the type of this unit. Note: this should not be done lightly. It is currently thought to be used only when the GUI changes the unit type table, and tries to create a clone of the current game state, but changing the UTT.
    public long getID() {} - Returns the unique identifier
    public void setID(long a_ID) {} - Changes the unique identifier Note: Do not use this function unless you know what you are doing!
    public int getPosition(PhysicalGameState pgs) {} - Returns the index of this unit in a {@link PhysicalGameState} (as it is an 'unrolled matrix')
    public int getX() {} - Returns the x coordinate
    public int getY() {} - Returns the y coordinate
    public void setX(int a_x) {} - Sets x coordinate
    public void setY(int a_y) {} - Sets y coordinate
    public int getResources() {} - Returns the amount of resources this unit is carrying
    public void setResources(int a_resources) {} - Sets the amount of resources the unit is carrying
    public int getHitPoints() {} - Returns the current HP
    public int getMaxHitPoints() {} - Returns the maximum HP this unit could have
    public void setHitPoints(int a_hitpoints) {} - Sets the amount of HP
    public int getCost() {} - The cost to produce this unit
    public int getMoveTime() {} - The time this unit gets to move
    public int getAttackTime() {} - The time it takes to perform an attack
    public int getAttackRange() {} - Returns the attack range
    public int getMinDamage() {} - Returns the minimum damage this unit's attack inflict
    public int getMaxDamage() {} - Returns the maximum damage this unit's attack inflict
    public int getHarvestAmount() {} - Returns the amount of resources this unit can harvest
    public int getHarvestTime() {} - The time it takes to harvest
    public boolean isIdle(GameState s) {} - Returns true if the unit is idle (i.e. if it's not executing any actions)
    public List<UnitAction> getUnitActions(GameState s) {} - Returns a list of actions this unit can perform in a given game state. An idle action for 10 cycles is always generated
    public List<UnitAction> getUnitActions(GameState s, int noneDuration) {} - Returns a list of actions this unit can perform in a given game state. An idle action for noneDuration cycles is always generated. noneDuration is the amount of cycles for the idle action that is always generated
    public boolean canExecuteAction(UnitAction ua, GameState gs) {} - Indicates whether this unit can perform an action in a given state
    public int hashCode() {} - Returns the unique ID
    }

rts.units.UnitTypeTable; - The unit type table stores the unit types the game can have. It also determines the attributes of each unit type. The unit type table determines the balance of the game.
 public class UnitTypeTable  {
    public static final int VERSION_ORIGINAL = 1; - Version one
    public static final int VERSION_ORIGINAL_FINETUNED = 2; - Version two (a fine tune of the original)
    public static final int VERSION_NON_DETERMINISTIC = 3; - A non-deterministic version (damages are random)
    public static final int MOVE_CONFLICT_RESOLUTION_CANCEL_BOTH = 1;   // (default) - A conflict resolution policy where move conflicts cancel both moves
    public static final int MOVE_CONFLICT_RESOLUTION_CANCEL_RANDOM = 2;   // (makes game non-deterministic) - A conflict resolution policy where move conflicts are solved randomly
    public static final int MOVE_CONFLICT_RESOLUTION_CANCEL_ALTERNATING = 3; - A conflict resolution policy where move conflicts are solved by alternating the units trying to move
    List<UnitType> unitTypes = new ArrayList<>(); - The list of unit types allowed in the game
    int moveConflictResolutionStrategy = MOVE_CONFLICT_RESOLUTION_CANCEL_BOTH; - Which move conflict resolution is being adopted
    public UnitTypeTable() {} - Creates a UnitTypeTable with version VERSION_ORIGINAL and move conflict resolution as MOVE_CONFLICT_RESOLUTION_CANCEL_BOTH
    public UnitTypeTable(int version) {} - Creates a unit type table with specified version and move conflict resolution as MOVE_CONFLICT_RESOLUTION_CANCEL_BOTH
    public UnitTypeTable(int version, int crs) {} - Creates a unit type table specifying both the version and the move conflict resolution strategy
    public void setUnitTypeTable(int version, int crs) {} - Sets the version and move conflict resolution strategy to use and configures the attributes of each unit type depending on the version
    public void addUnitType(UnitType ut) {} - Adds a new unit type to the game
    public UnitType getUnitType(int ID) {} - Retrieves a unit type by its numeric ID
    public UnitType getUnitType(String name) {} - Retrieves a unit type by its name. Returns null if name is not found.
    public List<UnitType> getUnitTypes() {} - Returns the list of all unit types
    public int getMoveConflictResolutionStrategy() {} - Returns the integer corresponding to the move conflict resolution strategy in use
    public int getMaxAttackRange() {} - Loop through the list of unit types and return the largest attack range
}
"""

signature= "public PlayerAction Harvest(GameState game, int player, PlayerAction currentPlayerAction, PathFinding pf, UnitTypeTable a_utt, HashMap<Long, String> counterByFunction)" 

header = """
import ai.synthesis.dslForScriptGenerator.IDSLParameters.IParameters;
import ai.abstraction.AbstractAction;
import ai.abstraction.Harvest;
import ai.abstraction.pathfinding.PathFinding;
import java.util.HashMap;
import java.util.HashSet;
import rts.GameState;
import rts.PhysicalGameState;
import rts.PlayerAction;
import rts.ResourceUsage;
import rts.UnitAction;
import rts.units.Unit;
import rts.units.UnitTypeTable;
"""

evolve = """
public PlayerAction Harvest_Resources(GameState game, int player, PlayerAction currentPlayerAction, PathFinding pf, UnitTypeTable a_utt, HashMap<Long, String> counterByFunction)
{
  PlayerAction pa = new PlayerAction();
  return pa;
}
"""

def get_code(funct):
 return """
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

""" + funct + """


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

"""


class LLM:
  """Language model that predicts continuation of provided source code."""

  def __init__(self, samples_per_prompt: int) -> None:
    self._samples_per_prompt = samples_per_prompt

  def _draw_sample(self, prompt: str) -> str:
    # """Returns a predicted continuation of `prompt`."""
    # api_url = "http://129.128.243.184:11434/api/generate"
    # headers = {"Content-Type": "application/json"}
    # payload = {"model": "deepseek-coder-v2-fixed:latest", "prompt": prompt, "stream": False, "template": "{{ .Prompt }}", "options": {"num_ctx": 8000, "stop": ["\ndef", "\nclass", "\n#", "\nimport"]}}
    # res = requests.post(api_url, headers=headers, json=payload, timeout=300)
    # # print(res["response"])

    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    model="deepseek-r1-distill-qwen-32b",
)
    c = chat_completion.choices[0].message.content
    # res = res.json()
    # print(c)
    # return res["response"]
    return parse(c)

  def draw_samples(self, prompt: str) -> Collection[str]:
    """Returns multiple predicted continuations of `prompt`."""
    return [self._draw_sample(prompt) for _ in range(self._samples_per_prompt)]


def pick_top_k_from_sampled_island(islands: list[list], scores: list[list[float]], k: int):
    # Step 1: Pick a random island index
    idx = random.randrange(len(islands))

    sampled_island = islands[idx]       # List of candidates
    sampled_scores = scores[idx]        # Corresponding scores

    # Step 2: Zip candidates with their scores
    paired = list(zip(sampled_island, sampled_scores))  # List of (candidate, score)

    # Step 3: Sort by score descending
    paired.sort(key=lambda x: x[1], reverse=True)

    # Step 4: Extract top-k candidates
    top_k_candidates = [cand for cand, _ in paired[:k]]

    return idx, top_k_candidates

def parse(out):
  out = out[out.find("```java")+7:]
  out = out[: out.find("```")]
  return out


def get_updated_prompt(version):
  number = 0
  prompt =  f"""
  {context}

  \n\n
  ------------------------------------------------------------------------- the file with the Harvest_Resources function begin below ------------------------------------------------
  \n\n


  {header}

  function to evolve version_{str(number)}

  {version[0]}

  \n\n
  -------------------------------------------------------------------------- only include evolved function code in your response  -----------------------------------------------------
  \n\n


  function to evolve version_{str(number+1)}
  \n
  {signature}{{}}
  \n\n

  """

  return prompt

def log_to_csv(island_id, iteration_num, best_funct, best_score, csv_filename='evolution_log.csv'):
    file_exists = os.path.isfile(csv_filename)

    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['island_id', 'iteration_num', 'function', 'score'])
        writer.writerow([island_id, iteration_num, repr(best_funct), best_score])


def sampler():
  llm = LLM(2)
  islands = [[evolve] for _ in range(4)]
  scores = [[0.0] for _ in range(4)]
  for i in range(100):
      island_id , version = pick_top_k_from_sampled_island(islands, scores, 1)
      prompt = get_updated_prompt(version[0])
      list_of_functions = llm.draw_samples(prompt)

      best_funct = list_of_functions[0]
      best_score = eval(list_of_functions[0])
      for funct in list_of_functions:
        score = eval(funct)
        if(score > best_score):
          best_funct = funct
          best_score = score

      islands[island_id].append(best_funct)
      scores[island_id].append(best_score)
      log_to_csv(island_id, i, best_funct, best_score)


def eval(funct):
    # Step 1: Get Java code
    java_code = get_code(funct)
    
    # Step 2: Create directories if they don't exist
    os.makedirs("src/tests", exist_ok=True)

    # Step 3: Write to src/tests/HarvestActionTest.java
    file_path = "src/tests/HarvestActionTest.java"
    with open(file_path, "w") as f:
        f.write(java_code)

    # Step 4: Compile the Java file with classpath
    compile_proc = subprocess.run(
        ["javac", "-cp", "bin/microRTS.jar", file_path],
        capture_output=True, text=True
    )

    if compile_proc.returncode != 0:
        # print(funct)
        # print("Compilation error:", compile_proc.stderr)
        with open("compile_error.log", "a") as err_file:
            err_file.write(f"Function: {funct}\n")
            err_file.write("Compilation error:\n")
            err_file.write(compile_proc.stderr)

        return -1.0

    print("Compiled successfully.")

    # Step 5: Run the Java class (with full package name if any)
    run_proc = subprocess.run(
        ["java", "-cp", "bin/microRTS.jar", file_path],
        capture_output=True, text=True
    )

    if run_proc.returncode == 0:
        try:
            result = float(run_proc.stdout.strip())
            return result
        except ValueError:
            print("Output is not a float:", run_proc.stdout)
            return -1.0
    else:
        print("Runtime error:", run_proc.stderr)
        return -1.0


# eval(evolve)
sampler()