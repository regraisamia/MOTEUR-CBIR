import React from 'react'

export default class ErrorBoundary extends React.Component{
  constructor(props){ super(props); this.state={error:null} }
  static getDerivedStateFromError(error){ return {error} }
  componentDidCatch(error, info){ console.error('ErrorBoundary', error, info) }
  render(){
    if(this.state.error) return (
      <div style={{padding:20}} className="card">
        <h3>Something went wrong</h3>
        <pre style={{whiteSpace:'pre-wrap',fontSize:12,color:'var(--red)'}}>{String(this.state.error)}</pre>
        <pre style={{whiteSpace:'pre-wrap',fontSize:11,color:'var(--text3)',marginTop:8}}>{this.state.error?.stack}</pre>
      </div>
    )
    return this.props.children
  }
}
