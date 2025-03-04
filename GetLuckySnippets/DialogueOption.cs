using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName = "Dialogue Data", menuName = "ScriptableObjects/Dialogue Data")]
public class DialogueOption : ScriptableObject
{
    public enum Stats
    {
        Charm,
        Int,
        Guilt,
        None
    }

    /// <summary>
    /// Full dialogue option
    /// </summary>
    [TextArea(10,20)]
    public string dialogueFull;

    /// <summary>
    /// Shorthanded dialogue displayed on the selection prompt
    /// </summary>
    public string dialogueShorthand;

    /// <summary>
    /// ID for the stat this dialogue represents
    /// </summary>
    public Stats statID;

    /// <summary>
    /// 
    /// </summary>
    public int statVal;

    /// <summary>
    /// If reaction, pose that Lady Luck will use
    /// </summary>
    public LadyLuckPoseManager.Pose pose;
}
