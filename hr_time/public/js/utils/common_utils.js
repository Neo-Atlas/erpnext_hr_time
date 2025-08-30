/**
 * @fileoverview Generic utility class for common JS methods.
 * @module JsUtils
 */

export class JsUtils{
  /**
   * Fetch saved value from local storage.
   * 
   * @param {string} key - The localStorage key associated with the value.
   */
  static getStringFromLocalStore = (key)=>{
    return localStorage.getItem(key)
  }

  /**
   * Save value to local storage.
   * 
   * @param {string} key - The unique key associated with the record.
   * @param {string} value - The value to persist in the local storage.
   */
  static saveStringToLocalStore = (key, value)=>{
    try{
      localStorage.setItem(key, value);
    } catch (error) {
        console.error('Failed to save in local storage:', error)
    }
  }
}