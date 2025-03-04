using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public interface ISavableSetting 
{
    void LoadSetting();

    void SaveSetting();

    void ResetSetting();
}
