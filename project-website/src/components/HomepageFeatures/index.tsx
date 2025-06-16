import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';
import Link from '@docusaurus/Link';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'YouTwo Architecture',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        Explore the comprehensive architecture of YouTwo, detailing its multi-source data ingestion, AI-powered knowledge processing, and intelligent query handling. <Link to="/docs/architecture">Learn More</Link>
      </>
    ),
  },
  {
    title: 'Multi-Source Knowledge Platform',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        YouTwo seamlessly integrates journal entries, uploaded documents, audio input, 
        and conversations into a unified knowledge base that evolves with your interactions.
      </>
    ),
  },
  {
    title: 'AI-Powered Insights',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Intelligent processing transforms raw information into meaningful insights with 
        automatic summarization, cross-document connections, and contextual retrieval.
      </>
    ),
  },
  {
    title: 'Conversational Interface',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        Ask questions naturally through voice or text and receive responses backed by 
        your personal knowledge with relevant citations and context-aware answers.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
