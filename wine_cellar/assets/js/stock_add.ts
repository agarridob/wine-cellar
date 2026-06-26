interface FreeCells {
  [storageId: string]: {
    [rows: string]: number[]
  }
}

function showWarning() {
  const warning = document.getElementById('storage__error-full')
  warning?.classList.remove('hidden')
}

function hideWarning() {
  const warning = document.getElementById('storage__error-full')
  warning?.classList.add('hidden')
}

function updateStorageCells() {
  const storageSelect = document.getElementById(
    'id_storage'
  ) as HTMLSelectElement
  const rowSelect = document.getElementById('id_row') as HTMLSelectElement
  const columnSelect = document.getElementById('id_column') as HTMLSelectElement
  const submitButton = document.getElementById(
    'submit_button'
  ) as HTMLButtonElement

  const storageData = document.getElementById('storage-data')
  if (!storageData) {
    console.error('storage-data element not found')
    return
  }
  const freeCells: FreeCells = JSON.parse(
    storageData.dataset.attributes || '{}'
  )

  if (storageSelect) {
    storageSelect.addEventListener('change', updateRows)
  }
  if (rowSelect) {
    rowSelect.addEventListener('change', updateColumns)
  }
  if (columnSelect) {
    columnSelect.addEventListener('change', updateSubmit)
  }

  function toggleFields(disable: boolean) {
    rowSelect.disabled = disable
    columnSelect.disabled = disable
    if (disable) {
      rowSelect.tomselect?.disable()
      columnSelect.tomselect?.disable()
    } else {
      rowSelect.tomselect?.enable()
      columnSelect.tomselect?.enable()
    }
    // Row/column are optional, so saving is always allowed.
    submitButton.disabled = false
  }

  function populateSelect(select: HTMLSelectElement, options: number[]) {
    select.innerHTML = ''
    options.forEach((val) => {
      const opt = document.createElement('option')
      opt.value = String(val)
      opt.textContent = String(val)
      select.appendChild(opt)
    })
    const ts = select.tomselect
    if (ts) {
      // Blank option = no specific slot (row/column are optional).
      ts.clear(true)
      ts.clearOptions()
      ts.addOption({ value: '', text: '—' })
      options.forEach((val) => ts.addOption({ value: val, text: val }))
      ts.refreshOptions(false)
      ts.setValue('', true)
    } else {
      const blank = document.createElement('option')
      blank.value = ''
      blank.textContent = '—'
      select.insertBefore(blank, select.firstChild)
      select.value = ''
    }
  }

  function updateSubmit() {
    submitButton.disabled = false
  }

  function updateColumns() {
    const storageId = storageSelect.value
    const rowId = rowSelect.value
    const storage = freeCells[storageId]
    if (!storage) {
      return
    }
    const columns = storage[rowId]
    if (!columns) {
      return
    }
    if (columns.length > 0) {
      populateSelect(columnSelect, columns)
      hideWarning()
    } else {
      showWarning()
      populateSelect(columnSelect, [])
    }
    toggleFields(false)
  }

  function updateRows() {
    const storageId = storageSelect.value
    const rows = freeCells[storageId]
    if (!rows) {
      return
    }
    const unlimitedShelf = Object.keys(rows).length === 0
    if (!unlimitedShelf) {
      const rowKeys = Object.keys(rows).map(Number)
      populateSelect(rowSelect, rowKeys)
      populateSelect(columnSelect, [])
      toggleFields(false)
    } else {
      populateSelect(rowSelect, [])
      populateSelect(columnSelect, [])
      toggleFields(true)
    }
  }
}

document.addEventListener('DOMContentLoaded', updateStorageCells)
