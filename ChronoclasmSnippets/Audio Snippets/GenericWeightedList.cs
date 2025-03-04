/* 
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - March 1st, 2022
 * Last Edited - March 1st, 2022 by Ben Schuster
 * Description - Generic weighted list that can be used for various systems later. 
 * Automatically handles the action of calculating probability and choosing an option
 * ================================================================================================
 */
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

[System.Serializable]
public class WeightedChoice<T>
{
    [Tooltip("The selection choice")]
    public T option;

    [Tooltip("The weight for this choice")]
    [Range(1, 1000)] public int weight = 1;

    [Tooltip("The esimate probability of this choice, as determined by its weight.")]
    [ReadOnly] public float estimateProbability = 0;
}


[System.Serializable]
public class GenericWeightedList<T>
{
    [ListDrawerSettings(Expanded = true, ShowItemCount = true)]
    [OnInspectorGUI("EstimateProbability")]
    [TableList(AlwaysExpanded = true, CellPadding = 7, HideToolbar = false)]
    [Tooltip("List of all weighted choices.")]
    public List<WeightedChoice<T>> weightedList;

    /// <summary>
    /// The odds for each chance. Used to generate estimate probability. 
    /// </summary>
    private float[] odds;

    public GenericWeightedList()
    {
        weightedList = new List<WeightedChoice<T>>();
    }

    /// <summary>
    /// Pull an object from this list at random
    /// </summary>
    /// <returns>Randomly selected object</returns>
    public T Pull()
    {
        // Skip randomness if no or one option
        if (weightedList.Count == 0)
            return default(T);
        else if (weightedList.Count == 1)
            return weightedList[0].option;

        // Get sum of all weights in list
        int total = 0;
        foreach (WeightedChoice<T> choice in weightedList)
            total += choice.weight;

        // Determine chances based on weights 
        float[] odds = new float[weightedList.Count];
        for (int i = 0; i < weightedList.Count; i++)
        {
            odds[i] = (float)weightedList[i].weight / total;
            weightedList[i].estimateProbability = odds[i] * 100;
        }

        // Roll the die, see which wins
        float ran = Random.Range(0f, 1f);
        float temp = 0;
        for(int i = 0; i < odds.Length; i++)
        {
            temp += odds[i];

            if(temp >= ran)
            {
                return weightedList[i].option;
            }
        }

        // Incase anything fails, return the last item. 
        // Above logic should always return something however as it should always add to 1. 
        return weightedList[weightedList.Count - 1].option;
    }

    /// <summary>
    /// Estimate the probability of all current weighted list options
    /// </summary>
    public void EstimateProbability()
    {
        // Get sum of all weights in list
        int total = 0;
        foreach (WeightedChoice<T> choice in weightedList)
            total += choice.weight;

        // Determine chances based on weights 
        float[] odds = new float[weightedList.Count];
        for (int i = 0; i < weightedList.Count; i++)
        {
            odds[i] = (float)weightedList[i].weight / total;
            weightedList[i].estimateProbability = odds[i] * 100;
        }
    }
}
