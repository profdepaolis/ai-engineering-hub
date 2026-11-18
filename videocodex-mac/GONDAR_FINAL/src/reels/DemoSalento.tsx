import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from 'remotion';
import type {Caption} from '../types';
import {
  AnimatedUnderline,
  GlobeLite,
  ImpactTitle,
  KineticCaption,
  PhotoShutter,
  SceneBackground,
  SearchBar,
  TypingTitle,
} from '../components';

const captions: Caption[] = [
  {text: 'Guarda', startMs: 200, endMs: 600},
  {text: 'il', startMs: 600, endMs: 750},
  {text: 'mare', startMs: 750, endMs: 1150, emphasis: true},
  {text: 'del', startMs: 1150, endMs: 1300},
  {text: 'Salento.', startMs: 1300, endMs: 1900, emphasis: true},
  {text: 'Tre', startMs: 2100, endMs: 2350},
  {text: 'foto,', startMs: 2350, endMs: 2600},
  {text: 'un', startMs: 2600, endMs: 2750},
  {text: 'solo', startMs: 2750, endMs: 3000},
  {text: 'impatto.', startMs: 3000, endMs: 3500},
  {text: 'Salento!', startMs: 3700, endMs: 4400, emphasis: true},
  {text: 'Da', startMs: 4600, endMs: 4800},
  {text: 'Lecce', startMs: 4800, endMs: 5200},
  {text: 'a', startMs: 5200, endMs: 5350},
  {text: 'Otranto,', startMs: 5350, endMs: 5800},
  {text: 'fino', startMs: 5800, endMs: 6000},
  {text: 'a', startMs: 6000, endMs: 6150},
  {text: 'Gallipoli.', startMs: 6150, endMs: 6800},
  {text: 'Cerca', startMs: 7000, endMs: 7300},
  {text: 'Grotta', startMs: 7300, endMs: 7700},
  {text: 'della', startMs: 7700, endMs: 7900},
  {text: 'Poesia', startMs: 7900, endMs: 8400, emphasis: true},
  {text: 'e', startMs: 8400, endMs: 8550},
  {text: 'scopri', startMs: 8550, endMs: 8850},
  {text: 'dove', startMs: 8850, endMs: 9050},
  {text: 'il', startMs: 9050, endMs: 9200},
  {text: 'mare', startMs: 9200, endMs: 9500},
  {text: 'incontra', startMs: 9500, endMs: 9850},
  {text: 'la', startMs: 9850, endMs: 10000},
  {text: 'storia.', startMs: 10000, endMs: 10500},
  {text: 'Pronto', startMs: 10700, endMs: 11000},
  {text: 'a', startMs: 11000, endMs: 11150},
  {text: 'partire?', startMs: 11150, endMs: 11800, emphasis: true},
];

const SceneShell: React.FC<{children: React.ReactNode}> = ({children}) => {
  return <AbsoluteFill>{children}</AbsoluteFill>;
};

export const DemoSalento: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {/* Scena 1 — Hook: typing + sottolineatura */}
      <Sequence from={0} durationInFrames={150}>
        <SceneShell>
          <SceneBackground gradient="linear-gradient(160deg,#0b3d5c,#062a40)" />
          <TypingTitle
            text="Guarda il mare del Salento"
            startFrame={6}
            endFrame={60}
            emphasisWord="mare"
          />
          <AnimatedUnderline startFrame={60} endFrame={90} top={1010} />
        </SceneShell>
      </Sequence>

      {/* Scena 2 — Foto che volano */}
      <Sequence from={150} durationInFrames={150}>
        <SceneShell>
          <SceneBackground gradient="linear-gradient(160deg,#3b2f5e,#1d1836)" />
          <PhotoShutter
            photos={[
              {label: '🏖️ Spiagge', gradient: 'linear-gradient(140deg,#f6d365,#fda085)', from: 15, to: 60, x: 90, y: 520, rotate: -6},
              {label: '⛪ Lecce', gradient: 'linear-gradient(140deg,#84fab0,#8fd3f4)', from: 45, to: 90, x: 300, y: 430, rotate: 5},
              {label: '🍷 Sapori', gradient: 'linear-gradient(140deg,#ff9a9e,#fecfef)', from: 75, to: 120, x: 190, y: 640, rotate: -2},
            ]}
          />
        </SceneShell>
      </Sequence>

      {/* Scena 3 — Impatto */}
      <Sequence from={300} durationInFrames={150}>
        <SceneShell>
          <SceneBackground gradient="linear-gradient(160deg,#5e2f2f,#2b1414)" />
          <ImpactTitle text="SALENTO!" startFrame={15} sub="dove il mare incontra la storia" />
        </SceneShell>
      </Sequence>

      {/* Scena 4 — Globo */}
      <Sequence from={450} durationInFrames={150}>
        <SceneShell>
          <GlobeLite startFrame={20} destinations={['Lecce', 'Otranto', 'Gallipoli']} />
        </SceneShell>
      </Sequence>

      {/* Scena 5 — Ricerca */}
      <Sequence from={600} durationInFrames={150}>
        <SceneShell>
          <SearchBar
            query="Grotta della Poesia"
            startFrame={15}
            resultFrame={100}
            resultTitle="Grotta della Poesia"
            resultSub="Risultato dimostrativo"
          />
        </SceneShell>
      </Sequence>

      {/* Scena 6 — CTA */}
      <Sequence from={750} durationInFrames={150}>
        <SceneShell>
          <SceneBackground gradient="linear-gradient(160deg,#0b3d5c,#062a40)" />
          <ImpactTitle text="Pronto a partire?" startFrame={15} fontSize={96} />
        </SceneShell>
      </Sequence>

      {/* Sottotitoli sempre attivi */}
      <KineticCaption captions={captions} />
      {/* Frame corrente per debug in Studio */}
      <div style={{display: 'none'}}>{frame}</div>
    </AbsoluteFill>
  );
};
