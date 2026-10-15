import type {ReactNode} from 'react';
export default function Panel({title,eyebrow,children,className=''}:{title:string;eyebrow?:string;children:ReactNode;className?:string}){return <section className={`panel ${className}`}><div className="panel-heading"><div>{eyebrow&&<div className="eyebrow">{eyebrow}</div>}<h2>{title}</h2></div><span className="panel-mark">●</span></div>{children}</section>}
