/* End-user upload wizard state machine. Upload transport remains owned by the existing upload API. */
(function(){
  'use strict';
  const STEPS=['modality','upload','validation','analysis','digital_twin'];
  const MODALITIES=['hand_images','hand_video','hand_3d','tissue_wsi','rna','proteomics','epigenetics','genomics'];
  let state={step:'modality',modality:null,files:[],validation:null,analysis:null};
  function setStep(step){if(STEPS.includes(step))state.step=step;return getState();}
  function chooseModality(modality){if(!MODALITIES.includes(modality))throw new Error('Unsupported modality');state.modality=modality;state.files=[];return setStep('upload');}
  function setFiles(files){state.files=Array.from(files||[]);return setStep('validation');}
  function setValidation(result){state.validation=result||null;return setStep(result?.valid===false?'validation':'analysis');}
  function setAnalysis(result){state.analysis=result||null;return setStep('digital_twin');}
  function reset(){state={step:'modality',modality:null,files:[],validation:null,analysis:null};return getState();}
  function getState(){return {...state,files:[...state.files]};}
  window.TestHPUserUploadWizard={STEPS,MODALITIES,setStep,chooseModality,setFiles,setValidation,setAnalysis,reset,getState};
})();
