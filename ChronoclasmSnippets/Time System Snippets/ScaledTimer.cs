/*
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - October 19th, 2022
 * Last Edited - October 19th, 2022 by Ben Schuster
 * Description - An independent timer class. Tracks its own time automatically.
 * ================================================================================================
 */
using UnityEngine;
using Masters.TimerSystem;

public class ScaledTimer 
{
    /// <summary>
    /// The target duration for this timer, in seconds.
    /// </summary>
    private float targetTime;
    /// <summary>
    /// The cached start time of this timer
    /// </summary>
    private float startTime;

    /// <summary>
    /// whether or not this timer is actually scaled
    /// </summary>
    private bool scaled;

    /// <summary>
    /// Timer speed modifier. % based, with 1 acting as 100%. cannot be 0
    /// </summary>
    private float timerModifier = 1;
    
    private float minModifier = 0;

    /// <summary>
    /// Create a new timer with 
    /// </summary>
    /// <param name="_targetTime">Target time for this value</param>
    /// <param name="_scaled">Whether this timer is scaled or not. Default true.</param>
    public ScaledTimer(float _targetTime, bool _scaled = true)
    {
        scaled = _scaled;
        if (scaled)
        {
            startTime = CoreTimeline.instance.ScaledTimeline;
        }
        else
        {
            startTime = CoreTimeline.instance.UnscaledTimeline;
        }

        targetTime = _targetTime;
    }

    /// <summary>
    /// Reset the active timer.
    /// </summary>
    public void ResetTimer()
    {
        if (CoreTimeline.instance == null) return;

        if (scaled)
        {
            startTime = CoreTimeline.instance.ScaledTimeline;
        }
        else
        {
            startTime = CoreTimeline.instance.UnscaledTimeline;
        }


        ResetTimer(targetTime);
    }

    /// <summary>
    /// Reset the timer and change the new target time.
    /// </summary>
    /// <param name="_newTargetTime">The new time to target</param>
    public void ResetTimer(float _newTargetTime)
    {
        ChangeTarget(_newTargetTime);

        if (scaled)
        {
            startTime = CoreTimeline.instance.ScaledTimeline;
        }
        else
        {
            startTime = CoreTimeline.instance.UnscaledTimeline;
        }
    }

    /// <summary>
    /// Change the target time. Does not reset the active timer.
    /// </summary>
    /// <param name="_newTargetTime">The new time to target</param>
    public void ChangeTarget(float _newTargetTime)
    {
        targetTime = _newTargetTime;
    }

    /// <summary>
    /// Gets whether the timer has reached its target time
    /// </summary>
    /// <returns>Whether or not this timer has finished</returns>
    public bool TimerDone()
    {
        if (timerModifier <= 0)
            return false;

        if(scaled)
        {
            return (CoreTimeline.instance.ScaledTimeline - startTime) >= (targetTime/ timerModifier);
        }
        else
        {
            return (CoreTimeline.instance.UnscaledTimeline - startTime) >= (targetTime/ timerModifier);
        }
    }

    /// <summary>
    /// Get the progress of the timer on a 0 to 1 scale.
    /// 0 is not done. 1 is done.
    /// </summary>
    /// <returns>% Progress of time passed. </returns>
    public float TimerProgress()
    {
        if (scaled)
        {
            return Mathf.Clamp((CoreTimeline.instance.ScaledTimeline - startTime) / (targetTime/ timerModifier), 0, 1);
        }
        else
        {
            return Mathf.Clamp((CoreTimeline.instance.UnscaledTimeline - startTime) / (targetTime/ timerModifier), 0, 1);
        }
    }

    /// <summary>
    /// Get the current target time for this timer
    /// </summary>
    /// <returns>The current target time</returns>
    public float CurrentTargetTime()
    {
        return targetTime;
    }

    /// <summary>
    /// Set the speed modifier for this timer 
    /// </summary>
    /// <param name="modifier">The new speed modifier to use</param>
    public void SetModifier(float modifier)
    {
        timerModifier = Mathf.Clamp(modifier, minModifier, Mathf.Infinity);
    }
    /// <summary>
    /// Increment the speed modifier for this timer
    /// </summary>
    /// <param name="modifier">Amount to increment the speed modifier by</param>
    public void IncrementModifier(float modifier)
    {
        timerModifier = Mathf.Clamp(timerModifier+modifier, minModifier, Mathf.Infinity);
    }
    /// <summary>
    /// Resets the timer's speed modifier back to normal
    /// </summary>
    public void ResetModifier()
    {
        SetModifier(1);
    }
}
