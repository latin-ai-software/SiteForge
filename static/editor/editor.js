// Enhanced editor: history, toolbar, proper drag-reorder, duplicate/delete, undo/redo
(function() {
  const palette = document.getElementById('block-palette')
  const canvasInner = document.getElementById('canvas-inner')
  const inspector = document.getElementById('inspector-content')
  const saveBtn = document.getElementById('save-page')
  const saveTop = document.getElementById('save-page-top')
  const undoBtn = document.getElementById('undo')
  const redoBtn = document.getElementById('redo')
  const page = document.getElementById('canvas').dataset.page

  // Simple history stack for undo/redo
  const history = {undo: [], redo: []}
  function snapshot(){
    const dsl = getDSL()
    history.undo.push(JSON.stringify(dsl))
    history.redo = []
    if(history.undo.length > 200) history.undo.shift()
  }
  function undo(){ if(!history.undo.length) return; history.redo.push(JSON.stringify(getDSL())); const prev = history.undo.pop(); loadFromDSL(JSON.parse(prev)) }
  function redo(){ if(!history.redo.length) return; history.undo.push(JSON.stringify(getDSL())); const next = history.redo.pop(); loadFromDSL(JSON.parse(next)) }

  function getDSL(){
    const blocks = []
    canvasInner.querySelectorAll('.block').forEach(b=>{
      const type = b.dataset.type
      const data = {}
      if(type === 'heading') data.text = b.querySelector('h2')?.innerText || ''
      if(type === 'hero') { data.title = b.querySelector('h1')?.innerText || ''; data.subtitle = b.querySelector('p')?.innerText || '' }
      blocks.push({type, data})
    })
    return {blocks}
  }

  function loadFromDSL(dsl){
    canvasInner.innerHTML = ''
    (dsl.blocks||[]).forEach(b=> canvasInner.appendChild(createBlock(b.type, b.data)))
  }

  function createBlock(type, data = {}){
    const el = document.createElement('div')
    el.className = 'block'
    el.dataset.type = type
    el.draggable = true
    el.id = 'b_' + Math.random().toString(36).slice(2,9)

    // Basic block markup
    if(type === 'heading'){
      const h = document.createElement('h2')
      h.contentEditable = true
      h.innerText = data.text || 'Heading'
      el.appendChild(h)
    } else if(type === 'hero'){
      const h = document.createElement('div')
      h.innerHTML = `<h1>${data.title || 'Site Title'}</h1><p>${data.subtitle || ''}</p>`
      el.appendChild(h)
    } else if(type === 'index_text'){
      el.innerText = 'Index text (preview)'
    } else if(type === 'post_list'){
      el.innerText = 'Post list (preview)'
    } else if(type === 'youtube'){
      el.innerText = 'YouTube videos (preview)'
    } else if(type === 'social_links'){
      el.innerText = 'Social links (preview)'
    } else {
      el.innerText = type
    }

    // Attach toolbar on hover/click
    el.addEventListener('mouseover', ()=>{ attachBlockToolbar(el) })

    el.addEventListener('click', (ev)=>{
      ev.stopPropagation()
      document.querySelectorAll('.block').forEach(b=>b.classList.remove('selected'))
      el.classList.add('selected')
      // Inspector
      if(type === 'hero'){
        inspector.innerHTML = `<div>Type: ${type}</div><label class='ins-label'>Title</label><input class='ins-input' id='ins-title' value='${data.title||''}'/><label class='ins-label'>Subtitle</label><input class='ins-input' id='ins-sub' value='${data.subtitle||''}'/><button id='ins-apply'>Apply</button>`
        document.getElementById('ins-apply').addEventListener('click', ()=>{
          const title = document.getElementById('ins-title').value
          const sub = document.getElementById('ins-sub').value
          el.querySelector('h1') && (el.querySelector('h1').innerText = title)
          el.querySelector('p') && (el.querySelector('p').innerText = sub)
        })
      } else {
        inspector.innerHTML = `<div>Type: ${type}</div><div>Options</div>`
      }
    })

    el.addEventListener('dragstart', (e)=>{
      e.dataTransfer.setData('application/x-block-id', el.id)
      e.dataTransfer.effectAllowed = 'move'
    })

    return el
  }

  // Palette: create new block
  palette.querySelectorAll('button').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      snapshot()
      const type = btn.dataset.blockType
      const b = createBlock(type)
      canvasInner.appendChild(b)
    })
  })

  // Canvas drag/drop: support moving existing blocks or dropping new ones
  canvasInner.addEventListener('dragover', (e)=>{ e.preventDefault(); e.dataTransfer.dropEffect='move' })
  canvasInner.addEventListener('drop', (e)=>{
    e.preventDefault()
    const id = e.dataTransfer.getData('application/x-block-id')
    const type = e.dataTransfer.getData('text/block')
    let target = e.target
    while(target && !target.classList?.contains('block') && target !== canvasInner) target = target.parentElement
    if(id){
      const node = document.getElementById(id)
      if(node){ snapshot(); if(target && target !== canvasInner) canvasInner.insertBefore(node, target.nextSibling); else canvasInner.appendChild(node) }
    } else if(type){
      snapshot(); const b = createBlock(type); if(target && target !== canvasInner) canvasInner.insertBefore(b, target.nextSibling); else canvasInner.appendChild(b)
    }
  })

  // Attach toolbar with actions to a block
  function attachBlockToolbar(el){
    if(el.querySelector('.block-toolbar')) return
    const tb = document.createElement('div')
    tb.className = 'block-toolbar'
    tb.innerHTML = `<button class='tb-up'>↑</button><button class='tb-down'>↓</button><button class='tb-dup'>⧉</button><button class='tb-del'>✕</button>`
    tb.style.position='absolute'; tb.style.right='8px'; tb.style.top='8px'; tb.style.display='flex'; tb.style.gap='6px'
    el.style.position = el.style.position || 'relative'
    el.appendChild(tb)
    tb.querySelector('.tb-del').addEventListener('click', (ev)=>{ ev.stopPropagation(); snapshot(); el.remove() })
    tb.querySelector('.tb-dup').addEventListener('click', (ev)=>{ ev.stopPropagation(); snapshot(); const clone = el.cloneNode(true); clone.id = 'b_'+Math.random().toString(36).slice(2,9); canvasInner.insertBefore(clone, el.nextSibling); attachBlockToolbar(clone) })
    tb.querySelector('.tb-up').addEventListener('click', (ev)=>{ ev.stopPropagation(); snapshot(); const prev = el.previousElementSibling; if(prev) canvasInner.insertBefore(el, prev) })
    tb.querySelector('.tb-down').addEventListener('click', (ev)=>{ ev.stopPropagation(); snapshot(); const next = el.nextElementSibling; if(next) canvasInner.insertBefore(next, el) })
  }

  // Observe newly added nodes to attach toolbar
  const obs = new MutationObserver((muts)=>{ muts.forEach(m=>{ m.addedNodes && m.addedNodes.forEach(n=>{ if(n.nodeType===1 && n.classList && n.classList.contains('block')) attachBlockToolbar(n) }) }) })
  obs.observe(canvasInner, {childList:true})

  function load(){ fetch(`/admin/editor/api/page/${page}`).then(r=>r.json()).then(data=>{ loadFromDSL(data) }) }

  function save(){
    const blocks = []
    canvasInner.querySelectorAll('.block').forEach(b=>{
      const type = b.dataset.type
      const data = {}
      if(type === 'heading') data.text = b.querySelector('h2')?.innerText || ''
      if(type === 'hero') { data.title = b.querySelector('h1')?.innerText || ''; data.subtitle = b.querySelector('p')?.innerText || '' }
      blocks.push({type, data})
    })
    fetch(`/admin/editor/api/page/${page}`, {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({blocks})}).then(r=>r.json()).then(resp=>{ alert('Saved') })
  }

  // Wire buttons
  saveBtn && saveBtn.addEventListener('click', save)
  saveTop && saveTop.addEventListener('click', save)
  undoBtn && undoBtn.addEventListener('click', undo)
  redoBtn && redoBtn.addEventListener('click', redo)
  document.addEventListener('keydown', (e)=>{ if((e.ctrlKey||e.metaKey) && e.key==='z'){ e.preventDefault(); undo() } if((e.ctrlKey||e.metaKey) && e.key==='y'){ e.preventDefault(); redo() } })

  load()
})()
