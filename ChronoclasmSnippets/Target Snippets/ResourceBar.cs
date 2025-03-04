/*
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - Februrary 1st, 2022
 * Last Edited - Februrary 1st, 2022 by Ben Schuster
 * Description - Controls a value contained within a resource bar
 * ================================================================================================
 */
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using Sirenix.OdinInspector;

public class ResourceBar
{
    protected enum State
    {
        UNINITIALIZED,
        FULL, 
        IDLE,
        EMPTIED,
        REGENERATING
    }

    [Header("Core Bar Info - READ ONLY")]

    private BarType _type;

    [SerializeField] private ResourceBarSO _barData;

    [SerializeField] private State _currState = State.UNINITIALIZED;

    [SerializeField] private float _maxAmount;
    [SerializeField] private float _currAmount;

    [SerializeField] private bool _regen;
    [HideIf("@this._regen == false")]
    [SerializeField] private bool _affectedByTimestop;
    [HideIf("@this._regen == false")]
    [SerializeField] private float _regenRate;
    [HideIf("@this._regen == false")]
    [SerializeField] private float _regenDelay;

    private ScaledTimer _regenTracker;

    private float timescale;

    public void Init(ResourceBarSO barInfo, float hpModifier = 1)
    {
        timescale = 1;
        _barData = barInfo;
        _type = barInfo._type;

        _maxAmount = barInfo._maxValue * hpModifier;
        _currAmount= _maxAmount;

        _regen = barInfo._regen;
        _affectedByTimestop = barInfo._affectedByTimestop;
        _regenRate = barInfo._regenRate * hpModifier;
        _regenDelay= barInfo._regenDelay;

        if (_regen)
            _regenTracker = new ScaledTimer(_regenDelay, false);

        // Set current state
        NonRegenStateCheck();
    }

    #region State Functionality

    /// <summary>
    /// Check what the current state should be, resetting any potential states.
    /// Used for taking damage or finishing healing.
    /// </summary>
    private void NonRegenStateCheck()
    {
        // Set current state
        if (_currAmount == _maxAmount)
        {
            ChangeState(State.FULL);
        }
        else if (_currAmount <= 0)
        {
            ChangeState(State.EMPTIED);
        }
        else
        {
            ChangeState(State.IDLE);
        }
    }

    public void SetTimesale(float newScale)
    {
        if(_affectedByTimestop)
        {
            timescale = newScale;
            _regenTracker?.SetModifier(timescale);
        }
    }

    /// <summary>
    /// Change the current state, activate any cross-section functionality
    /// </summary>
    public void StateUpdateFunction()
    {
        switch (_currState)
        {
            case State.FULL:
                {
                    break;
                }
            case State.IDLE:
                {
                    if(CheckRegen())
                    {
                        ChangeState(State.REGENERATING);
                    }

                    break;
                }
            case State.EMPTIED:
                {
                    if (CheckRegen())
                    {
                        ChangeState(State.REGENERATING);
                    }

                    break;
                }
            case State.REGENERATING:
                {
                    RegenTick();
                    if (IsFull())
                        ChangeState(State.FULL);

                    break;
                }
            default:
                {
                    break;
                }
        }
    }


    /// <summary>
    /// Change the state and perform any cross-function functionality
    /// </summary>
    /// <param name="newState">New state to move to</param>
    private void ChangeState(State newState)
    {
        switch (newState)
        {
            case State.FULL:
                {
                    ResetRegenRate();
                    break;
                }
            case State.IDLE:
                {
                    ResetRegenRate();
                    break;
                }
            case State.EMPTIED:
                {
                    ResetRegenRate();
                    break;
                }
            case State.REGENERATING:
                {
                    break;
                }
        }

        _currState = newState;
    }

    

    #endregion

    #region Current Value Modifying Functions

    /// <summary>
    /// Decrease the current gauge of this resource bar
    /// </summary>
    /// <param name="amt">amount to reduce this resource by</param>
    /// <returns>Overflow after decreasing this gauge to 0</returns>
    public float Decrease(float amt)
    {
        if(_currAmount - amt >= 0)
        {
            _currAmount -= amt;

            //ResetRegenRate();
            NonRegenStateCheck();
            return 0;
        }
        else
        {
            float overflow = amt - _currAmount;
            _currAmount = 0;

            //ResetRegenRate();
            NonRegenStateCheck();
            return overflow;
        }
    }
    /// <summary>
    /// Increase the current gauge of this resource bar
    /// </summary>
    /// <param name="amt">amount to increase this resource by</param>
    /// <returns>Overflow after increasing this gauge to max</returns>
    public float Increase(float amt)
    {
        if (_currAmount + amt <= _maxAmount)
        {
            _currAmount += amt;

            return 0;
        }
        else
        {
            float overflow = amt - (_maxAmount - _currAmount);
            _currAmount = _maxAmount;

            return overflow;
        }
    }

    #endregion

    #region Getters

    public BarType Type()
    {
        return _type;
    }

    public bool IsFull()
    {
        return _currAmount == _maxAmount;
    }

    public bool IsEmptied()
    {
        return _currAmount <= 0;
    }
    
    public float CurrentValue()
    {
        return _currAmount;
    }

    public float MaxValue()
    {
        return _maxAmount;
    }

    public ResourceBarSO BarData
    {
        get { return _barData;}
    }

    #endregion

    #region Regenerating functions
    
    /// <summary>
    /// Check if this bar can regenerate naturally
    /// </summary>
    /// <returns>Whether this bar can begin regenerating</returns>
    private bool CheckRegen()
    {
        if(!_regen)
        {
            return false;
        }
        else
        {
            return _regenTracker.TimerDone();
        }
    }

    public void ResetRegenRate()
    {
        if(_regen)
            _regenTracker.ResetTimer();
    }

    /// <summary>
    /// Regenerate 1 tick of this resource bar
    /// </summary>
    private void RegenTick()
    {
        // If not allowed to regen, then exit
        if (!_regen)
            return;

        // calculate amount to recharge, rounding down. Add to buffer
        float replenishAmount = (_maxAmount / _regenRate) / 50;

        // scale in timestop
        if (_affectedByTimestop)
            replenishAmount *= timescale;

        // Replenish the gauge, determine if state should change
        Increase(replenishAmount);
    }

    #endregion

    #region UpgradeFunctions

    /// <summary>
    /// Increment the maximum of this resource bar
    /// </summary>
    /// <param name="increment">Amount to incremenent health by</param>
    /// <param name="increaseCurrent">Whether to increase the current by the same amount</param>
    public void IncreaseMax(float increment, bool increaseCurrent)
    {
        _maxAmount += increment;

        if(increaseCurrent)
        {
            _currAmount += increment;
        }

        NonRegenStateCheck();
    }

    /// <summary>
    /// Decrement the maximum of this resource bar
    /// </summary>
    /// <param name="decrement">Amount to incremenent health by</param>
    /// <param name="decreaseCurrent">Whether to increase the current by the same amount</param>
    public void DecreaseMax(float decrement)
    {
        _maxAmount -= decrement;
        // ensure that low health players won't instantly die on removing a crystal that increases max health
        // done because just allowing them to keep the hp opens up exploits
        // eg equipping and dequipping the crystal many times in a row to heal

        _currAmount = Mathf.Clamp(_currAmount, 1, _maxAmount);
        
        NonRegenStateCheck();
    }

    /// <summary>
    /// Set the maximum of this resource bar
    /// </summary>
    /// <param name="max">New max to set the resource bar to</param>
    /// <param name="newCurr">New current value to set this bar to</param>
    public void SetMax(float max, float newCurr = -1)
    {
        _maxAmount = max;

        if(newCurr >= 0)
            _currAmount = Mathf.Clamp(newCurr, 0, _maxAmount);

        NonRegenStateCheck();
    }

    #endregion
}
