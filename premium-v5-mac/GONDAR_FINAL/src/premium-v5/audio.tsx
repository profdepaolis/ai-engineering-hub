import {Audio,staticFile} from 'remotion';
import {auditDirector,type Director} from './core';
/** Consumes the sample-aligned VOICEOVER+SFX master produced by premium_tools.py mix. */
export const SoundDesignTrack=({director,mixPath}:{director:Director;mixPath:string})=>{const audit=auditDirector(director);if(!audit.passed)throw Error(audit.errors.join('; '));return <Audio src={staticFile(mixPath)}/>;};
