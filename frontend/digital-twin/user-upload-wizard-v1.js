/* End-user upload wizard. Transport stays owned by the existing upload API. */
(function(){
  'use strict';
  const STEPS=['modality','upload','validation','analysis','digital_twin'];
  const MODALITIES=['hand_images','hand_video','hand_3d','tissue_wsi','rna','proteomics','epigenetics','genomics'];
  let state={step:'modality',modality:null,files:[],validation:null,analysis:null};
  function publish(){
    const snapshot=getState();
    window.dispatchEvent(new CustomEvent('testhp:upload-wizard-changed',{detail:snapshot}));
    if(window.TestHPCanonicalState?.setUserInput) window.TestHPCanonicalState.setUserInput({modalities:{[state.modality]:state.files.length?{files:state.files}:null}});
    return snapshot;
  }
  function setStep(step){if(!STEPS.includes(step))throw new Error('Unsupported wizard step');state.step=step;return publish();}
  function chooseModality(modality){if(!MODALITIES.includes(modality))throw new Error('Unsupported modality');state.modality=modality;state.files=[];state.validation=null;state.analysis=null;return setStep('upload');}
  function setFiles(files){state.files=Array.from(files||[]);return setStep('validation');}
  function setValidation(result){state.validation=result||null;return setStep(result?.valid===false?'validation':'analysis');}
  function setAnalysis(result){state.analysis=result||null;window.dispatchEvent(new CustomEvent('testhp:analysis-result',{detail:result}));return setStep('digital_twin');}
  function reset(){state={step:'modality',modality:null,files:[],validation:null,analysis:null};if(window.TestHPCanonicalState?.reset)window.TestHPCanonicalState.reset();return publish();}
  function getState(){return {...state,files:[...state.files]};}
  window.TestHPUserUploadWizard={STEPS,MODALITIES,setStep,chooseModality,setFiles,setValidation,setAnalysis,reset,getState};
})();
